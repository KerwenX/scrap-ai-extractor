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
        extracted_fields=["title", "abstract"],
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


def test_controller_lists_builtin_templates():
    controller = ExtractionController()
    payload = controller.list_templates()
    template_ids = {item["template_id"] for item in payload["templates"]}
    assert "dayi_disease_v1" in template_ids
    assert "dayi_qa_v1" in template_ids


def test_controller_manages_templates_and_candidates(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    candidate = _build_candidate("candidate-1")
    service.persist_candidate(candidate)
    manifest = service.solidify_candidate(candidate, required_fields=["title"])
    assert manifest is not None

    controller = ExtractionController(template_service=service)
    templates_payload = controller.list_templates()
    assert any(item["template_id"] == manifest.template_id for item in templates_payload["templates"])

    template_payload = controller.get_template(manifest.template_id)
    assert template_payload["active"] is True
    assert template_payload["lifecycle_status"] == "active"

    updated = controller.set_template_active(manifest.template_id, False)
    assert updated["active"] is False
    assert updated["lifecycle_status"] == "deprecated"

    reactivated = controller.set_template_status(manifest.template_id, "active")
    assert reactivated["active"] is True
    assert reactivated["lifecycle_status"] == "active"

    archived = controller.set_template_status(manifest.template_id, "archived")
    assert archived["active"] is False
    assert archived["lifecycle_status"] == "archived"

    candidates_payload = controller.list_template_candidates()
    assert any(item["candidate_id"] == candidate.candidate_id for item in candidates_payload["candidates"])
    listed_candidate = next(item for item in candidates_payload["candidates"] if item["candidate_id"] == candidate.candidate_id)
    assert listed_candidate["promotion_check"]["promotable"] is False
    assert listed_candidate["promotion_check"]["existing_template_id"] == manifest.template_id

    candidate_payload = controller.get_template_candidate(candidate.candidate_id)
    assert candidate_payload["sample_data"]["title"] == "Paper title"
    assert candidate_payload["promotion_check"]["promotable"] is False
    assert candidate_payload["promotion_check"]["existing_template_id"] == manifest.template_id


def test_controller_promotes_candidate_with_versioned_template_key(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    first_candidate = _build_candidate("candidate-1", dom_signature="abc123")
    second_candidate = _build_candidate("candidate-2", dom_signature="def456").model_copy(
        update={"sample_data": {"title": "Paper title 2"}}
    )
    service.persist_candidate(first_candidate)
    service.persist_candidate(second_candidate)
    controller = ExtractionController(template_service=service)

    first_manifest = controller.promote_template_candidate(
        first_candidate.candidate_id,
        {
            "template_key": "paper_detail",
            "required_fields": ["title"],
            "deactivate_previous_versions": True,
        },
    )
    second_manifest = controller.promote_template_candidate(
        second_candidate.candidate_id,
        {
            "template_key": "paper_detail",
            "required_fields": ["title"],
            "deactivate_previous_versions": True,
        },
    )

    assert first_manifest["template_id"] == "paper_detail_v1"
    assert second_manifest["template_id"] == "paper_detail_v2"
    assert second_manifest["template_key"] == "paper_detail"
    assert second_manifest["source_candidate_id"] == second_candidate.candidate_id
    assert controller.get_template("paper_detail_v1")["active"] is False
    assert controller.get_template("paper_detail_v1")["lifecycle_status"] == "deprecated"
    assert controller.get_template("paper_detail_v2")["active"] is True


def test_controller_deletes_single_and_multiple_templates(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    first_candidate = _build_candidate("candidate-1", dom_signature="abc123")
    second_candidate = _build_candidate("candidate-2", dom_signature="def456")
    service.persist_candidate(first_candidate)
    service.persist_candidate(second_candidate)
    first_manifest = service.solidify_candidate(first_candidate, required_fields=["title"])
    second_manifest = service.solidify_candidate(second_candidate, required_fields=["title"])
    assert first_manifest is not None
    assert second_manifest is not None

    controller = ExtractionController(template_service=service)
    deleted = controller.delete_template(first_manifest.template_id)
    assert deleted["deleted"] is True
    assert controller.get_template(second_manifest.template_id)["template_id"] == second_manifest.template_id

    batch_deleted = controller.delete_templates({"template_ids": [second_manifest.template_id, "missing"]})
    assert batch_deleted["deleted_count"] == 1


def test_controller_deletes_candidate(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    candidate = _build_candidate("candidate-1")
    service.persist_candidate(candidate)
    controller = ExtractionController(template_service=service)
    deleted = controller.delete_template_candidate(candidate.candidate_id)
    assert deleted["deleted"] is True


def test_template_key_auto_generation_uses_page_type_and_url_hash_family_key(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    candidate = _build_candidate("candidate-1", dom_signature="abc123def4567890")
    manifest = service.solidify_candidate(candidate, required_fields=["title"])
    assert manifest is not None
    assert manifest.template_key.startswith("example_com_article_detail_detail_page_")
    assert not manifest.template_key.endswith("_abc123def456")
    assert manifest.required_fields == ["title"]


def test_controller_reports_candidate_not_promotable_reason(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    candidate = _build_candidate("candidate-1").model_copy(
        update={"proposed_plan": None}
    )
    service.persist_candidate(candidate)
    controller = ExtractionController(template_service=service)

    listed = controller.list_template_candidates()["candidates"][0]
    assert listed["promotion_check"]["promotable"] is False
    assert "proposed_plan" in listed["promotion_check"]["reasons"][0]

    try:
        controller.promote_template_candidate(candidate.candidate_id, {})
    except ValueError as exc:
        assert "not promotable" in str(exc)
        assert "proposed_plan" in str(exc)
    else:
        raise AssertionError("Expected promotion to fail for candidate without proposed_plan")
