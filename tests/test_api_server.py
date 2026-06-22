import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from hybrid_extractor.api_server import ApiHandler, ThreadingHTTPServer
from hybrid_extractor.controllers import ExtractionController
from hybrid_extractor.models import (
    ExtractionPlan,
    FieldRule,
    FieldSelectorRule,
    PageFingerprint,
    TemplateCandidate,
)
from hybrid_extractor.services.template_service import TemplateService


def _build_candidate(candidate_id: str, dom_signature: str = "abc123") -> TemplateCandidate:
    return TemplateCandidate(
        candidate_id=candidate_id,
        request_id=f"req-{candidate_id}",
        site_id="example.com",
        site_name="example.com",
        page_type="detail_page",
        scenario="article_detail",
        user_prompt="提取标题和摘要",
        source_url="https://example.com/paper/1",
        fingerprint=PageFingerprint(
            dom_signature=dom_signature,
            headings=["Title"],
            key_ids=[],
            key_classes=[],
        ),
        extracted_fields=["title"],
        sample_data={"title": "Paper title"},
        proposed_plan=ExtractionPlan(
            fields=[
                FieldRule(
                    field_name="title",
                    selectors=[FieldSelectorRule(kind="css", value="h1")],
                )
            ]
        ),
    )


def test_api_server_health_and_template_management_responses():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        service = TemplateService(
            template_dir=root / "templates",
            template_store_dir=root / "template_store",
            template_candidate_dir=root / "template_candidates",
        )
        candidate = _build_candidate("candidate-1", "abc123")
        promote_candidate = _build_candidate("candidate-2", "def456").model_copy(
            update={"sample_data": {"title": "Paper title 2"}}
        )
        delete_candidate = _build_candidate("candidate-3", "ghi789")
        service.persist_candidate(candidate)
        service.persist_candidate(promote_candidate)
        service.persist_candidate(delete_candidate)
        manifest = service.solidify_candidate(candidate, required_fields=["title"])
        assert manifest is not None

        original_controller = ApiHandler.controller
        ApiHandler.controller = ExtractionController(template_service=service)
        server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with urllib.request.urlopen(f"{base_url}/health") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["status"] == "ok"

            with urllib.request.urlopen(f"{base_url}/") as response:
                html = response.read().decode("utf-8")
                assert "<title>混合网页解析器</title>" in html
                assert "批量模板解析" in html
                assert 'id="detailSummary"' in html
                assert "buildDetailSummary" in html
                assert 'id="progressList"' in html
                assert "pushResponseProgress" in html

            with urllib.request.urlopen(f"{base_url}/templates") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert any(item["template_id"] == manifest.template_id for item in payload["templates"])

            with urllib.request.urlopen(f"{base_url}/template-candidates") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert any(item["candidate_id"] == candidate.candidate_id for item in payload["candidates"])
                listed_candidate = next(item for item in payload["candidates"] if item["candidate_id"] == candidate.candidate_id)
                assert listed_candidate["promotion_check"]["promotable"] is True
                assert listed_candidate["promotion_check"]["action"] == "create"
                assert listed_candidate["promotion_check"]["existing_template_id"] is None

            promote_body = json.dumps(
                {
                    "template_key": "paper_detail",
                    "required_fields": ["title"],
                    "deactivate_previous_versions": True,
                }
            ).encode("utf-8")
            promote_request = urllib.request.Request(
                f"{base_url}/template-candidates/{promote_candidate.candidate_id}/promote",
                data=promote_body,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(promote_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["template_id"] == "paper_detail_v1"
                assert payload["template_key"] == "paper_detail"

            batch_delete_request = urllib.request.Request(
                f"{base_url}/templates/delete-batch",
                data=json.dumps({"template_ids": [manifest.template_id, "paper_detail_v1"]}).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(batch_delete_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["deleted_count"] == 2

            candidate_delete_request = urllib.request.Request(
                f"{base_url}/template-candidates/{delete_candidate.candidate_id}",
                method="DELETE",
            )
            with urllib.request.urlopen(candidate_delete_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["deleted"] is True

            bad_json_request = urllib.request.Request(
                f"{base_url}/extract",
                data=b'{"bad_json"',
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                urllib.request.urlopen(bad_json_request)
            except urllib.error.HTTPError as exc:
                payload = json.loads(exc.read().decode("utf-8"))
                assert exc.code == 400
                assert payload["error"] == "Invalid JSON body"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            ApiHandler.controller = original_controller


def test_api_server_batch_extract_requires_url_and_writes_result_file():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        html_path = root / "sample.html"
        html_path.write_text("<html><body><h1>Sample</h1></body></html>", encoding="utf-8")

        service = TemplateService(
            template_dir=root / "templates",
            template_store_dir=root / "template_store",
            template_candidate_dir=root / "template_candidates",
        )

        original_controller = ApiHandler.controller
        ApiHandler.controller = ExtractionController(template_service=service)
        server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            output_path = root / "results.jsonl"
            batch_request = urllib.request.Request(
                f"{base_url}/extract/batch",
                data=json.dumps(
                    {
                        "jsonl_content": json.dumps(
                            {
                                "url": "https://example.com/a",
                                "html_path": str(html_path),
                            },
                            ensure_ascii=False,
                        ),
                        "user_prompt": "提取标题",
                        "output_jsonl_path": str(output_path),
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(batch_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["output_jsonl_path"] == str(output_path)
                assert payload["total_count"] == 1
                assert Path(payload["output_jsonl_path"]).exists()
                line = json.loads(Path(payload["output_jsonl_path"]).read_text(encoding="utf-8").strip())
                assert line["url"] == "https://example.com/a"
                assert line["extractor_type"] in {"none", "deterministic"}

            invalid_batch_request = urllib.request.Request(
                f"{base_url}/extract/batch",
                data=json.dumps(
                    {
                        "jsonl_content": json.dumps({"html_path": str(html_path)}, ensure_ascii=False),
                        "user_prompt": "提取标题",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                urllib.request.urlopen(invalid_batch_request)
            except urllib.error.HTTPError as exc:
                payload = json.loads(exc.read().decode("utf-8"))
                assert exc.code == 400
                assert "missing url" in payload["error"]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            ApiHandler.controller = original_controller
