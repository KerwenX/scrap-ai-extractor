from hybrid_extractor.controllers import ExtractionController
from hybrid_extractor.engine import HybridExtractionEngine
from hybrid_extractor.extractors.base import BaseFallbackExtractor
from hybrid_extractor.fingerprinting import build_fingerprint
from hybrid_extractor.models import (
    ExtractionIntent,
    ExtractionPlan,
    ExtractionRequest,
    ExtractionResult,
    FieldRule,
    FieldSelectorRule,
    PageFingerprint,
    TemplateCandidate,
    TemplateManifest,
)
from hybrid_extractor.preprocessing import build_soup, clean_html
from hybrid_extractor.services.template_service import TemplateService


def _candidate_with_fields(candidate_id: str, dom_signature: str, field_names: list[str]) -> TemplateCandidate:
    selector_map = {
        "title": "h1",
        "abstract": ".abstract",
        "author": ".author",
        "publish_time": ".time",
    }
    return TemplateCandidate(
        candidate_id=candidate_id,
        request_id=f"req-{candidate_id}",
        site_id="example.com",
        site_name="example.com",
        page_type="detail_page",
        scenario="detail_page",
        user_prompt="提取论文信息",
        source_url="https://example.com/paper/1",
        fingerprint=PageFingerprint(
            dom_signature=dom_signature,
            headings=["Paper"],
            key_ids=["content"],
            key_classes=["abstract"],
        ),
        extracted_fields=field_names,
        sample_data={name: f"value-{name}" for name in field_names},
        proposed_plan=ExtractionPlan(
            fields=[
                FieldRule(
                    field_name=name,
                    selectors=[FieldSelectorRule(kind="css", value=selector_map.get(name, "body"))],
                )
                for name in field_names
            ]
        ),
    )


def test_same_fingerprint_candidate_is_upgradeable_when_plan_is_richer(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    weak_candidate = _candidate_with_fields("weak", "same123", ["title"])
    strong_candidate = _candidate_with_fields(
        "strong",
        "same123",
        ["title", "abstract", "author", "publish_time"],
    )
    original = service.promote_candidate_instance(
        weak_candidate,
        template_key="paper_detail",
        required_fields=["title"],
    )
    assert original is not None
    service.persist_candidate(strong_candidate)

    check = service.inspect_candidate_promotability(strong_candidate)
    assert check["promotable"] is True
    assert check["action"] == "upgrade"
    assert check["existing_template_id"] == "paper_detail_v1"

    controller = ExtractionController(template_service=service)
    upgraded = controller.promote_template_candidate(
        strong_candidate.candidate_id,
        {"template_key": "paper_detail", "deactivate_previous_versions": True},
    )
    assert upgraded["template_id"] == "paper_detail_v2"
    assert controller.get_template("paper_detail_v1")["active"] is False
    assert controller.get_template("paper_detail_v2")["active"] is True


def test_engine_auto_upgrades_weak_template_after_llm_success(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <body>
        <h1>Paper One</h1>
        <div class="abstract">Paper abstract</div>
        <div class="author">Alice</div>
        <div class="time">2026-06-21</div>
      </body>
    </html>
    """
    fingerprint = build_fingerprint(build_soup(clean_html(html)))
    weak_manifest = TemplateManifest(
        template_id="paper_family_v1",
        parser_key="generic:rule",
        site_id="example.com",
        site_name="example.com",
        page_type="detail_page",
        scenario="detail_page",
        version="v1",
        template_key="paper_family",
        lifecycle_status="active",
        active=True,
        fingerprint=fingerprint,
        required_fields=["title", "abstract"],
        extraction_plan=ExtractionPlan(
            fields=[
                FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                FieldRule(
                    field_name="abstract",
                    selectors=[FieldSelectorRule(kind="css", value=".missing-abstract")],
                ),
            ]
        ),
    )
    service.upsert_manifest(weak_manifest)

    class RichPaperFallbackExtractor(BaseFallbackExtractor):
        def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
            return ExtractionResult(
                data={
                    "title": "Paper One",
                    "abstract": "Paper abstract",
                    "author": "Alice",
                    "publish_time": "2026-06-21",
                }
            )

    engine = HybridExtractionEngine(
        fallback_extractor=RichPaperFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/paper/1",
        raw_html=html,
        user_prompt="extract title, abstract, author and publish time",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "hybrid"
    assert response.debug_trace["solidified_template_id"] == "paper_family_v2"
    assert service.get_manifest("paper_family_v1").active is False
    upgraded = service.get_manifest("paper_family_v2")
    assert upgraded is not None
    assert upgraded.extraction_plan is not None
    assert len(upgraded.extraction_plan.fields) >= 4
