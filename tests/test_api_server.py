import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from hybrid_extractor.api_server import ApiHandler, ThreadingHTTPServer
from hybrid_extractor.controllers import ExtractionController
from hybrid_extractor.models import ExtractionPlan, FieldRule, FieldSelectorRule, PageFingerprint, TemplateCandidate
from hybrid_extractor.services.template_service import TemplateService


def test_api_server_health_and_validation_responses():
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        service = TemplateService(
            template_dir=root / "templates",
            template_store_dir=root / "template_store",
            template_candidate_dir=root / "template_candidates",
        )
        candidate = TemplateCandidate(
            request_id="req-1",
            site_id="example.com",
            site_name="example.com",
            page_type="detail_page",
            scenario="article_detail",
            user_prompt="提取标题和摘要",
            source_url="https://example.com/paper/1",
            fingerprint=PageFingerprint(dom_signature="abc123", headings=["Title"], key_ids=[], key_classes=[]),
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
        service.persist_candidate(candidate)
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
                assert "<title>" in html

            with urllib.request.urlopen(f"{base_url}/templates") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert any(item["template_id"] == manifest.template_id for item in payload["templates"])

            with urllib.request.urlopen(f"{base_url}/templates/{manifest.template_id}") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["template_id"] == manifest.template_id

            with urllib.request.urlopen(f"{base_url}/template-candidates") as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert any(item["candidate_id"] == candidate.candidate_id for item in payload["candidates"])

            toggle_request = urllib.request.Request(
                f"{base_url}/templates/{manifest.template_id}/deactivate",
                data=b"{}",
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(toggle_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert payload["active"] is False

            request = urllib.request.Request(
                f"{base_url}/extract",
                data=b'{"bad_json"',
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                urllib.request.urlopen(request)
            except urllib.error.HTTPError as exc:
                payload = json.loads(exc.read().decode("utf-8"))
                assert exc.code == 400
                assert payload["error"] == "Invalid JSON body"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            ApiHandler.controller = original_controller
