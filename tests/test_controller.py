from hybrid_extractor.controllers import ExtractionController


def test_controller_lists_builtin_templates():
    controller = ExtractionController()
    payload = controller.list_templates()
    template_ids = {item["template_id"] for item in payload["templates"]}
    assert "dayi_disease_v1" in template_ids
    assert "dayi_qa_v1" in template_ids
