from hybrid_extractor.models import ExtractionIntent
from hybrid_extractor.prompts import (
    build_extraction_prompt,
    build_template_analysis_prompt,
    build_template_plan_prompt,
)


def test_build_extraction_prompt_includes_contract_and_user_requirement():
    intent = ExtractionIntent(
        entity_type=None,
        requested_capabilities=["title", "summary", "authors"],
        normalized_prompt="\u63d0\u53d6\u75be\u75c5\u75c7\u72b6\u548c\u6cbb\u7597",
    )
    prompt = build_extraction_prompt(intent)
    assert "Return valid JSON only" in prompt
    assert "title, summary, authors" in prompt
    assert "\u63d0\u53d6\u75be\u75c5\u75c7\u72b6\u548c\u6cbb\u7597" in prompt
    assert "prefer Chinese field names" in prompt
    assert "\u6807\u9898\u3001\u4f5c\u8005\u3001\u6458\u8981\u3001\u533b\u751f" in prompt


def test_build_template_plan_prompt_includes_fields():
    prompt = build_template_plan_prompt("extract disease info", ["name", "symptoms"])
    assert "portable selectors" in prompt
    assert "name, symptoms" in prompt


def test_build_template_analysis_prompt_includes_analysis_stage():
    prompt = build_template_analysis_prompt("extract disease info", ["name", "symptoms"])
    assert "Analyze before proposing extraction rules" in prompt
    assert "name, symptoms" in prompt
