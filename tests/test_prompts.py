from hybrid_extractor.models import ExtractionIntent
from hybrid_extractor.prompts import build_extraction_prompt, build_template_plan_prompt


def test_build_extraction_prompt_includes_contract_and_user_requirement():
    intent = ExtractionIntent(
        entity_type="disease_page",
        requested_capabilities=["symptoms"],
        normalized_prompt="\u63d0\u53d6\u75be\u75c5\u75c7\u72b6\u548c\u6cbb\u7597",
    )
    prompt = build_extraction_prompt(intent)
    assert "Return valid JSON only" in prompt
    assert "name, summary, aliases" in prompt
    assert "\u63d0\u53d6\u75be\u75c5\u75c7\u72b6\u548c\u6cbb\u7597" in prompt


def test_build_template_plan_prompt_includes_fields():
    prompt = build_template_plan_prompt("extract disease info", ["name", "symptoms"])
    assert "portable selectors" in prompt
    assert "name, symptoms" in prompt
