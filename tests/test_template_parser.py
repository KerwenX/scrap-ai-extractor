from pathlib import Path

from hybrid_extractor.models import ExtractionRequest
from hybrid_extractor.preprocessing import build_soup, extract_page_title
from hybrid_extractor.templates.dayi_disease import DayiDiseaseTemplateParser
from hybrid_extractor.templates.dayi_qa import DayiQATemplateParser
from hybrid_extractor.classification import PageClassifier


def test_dayi_template_match_and_extract():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息、病因、症状、诊断、治疗和预防",
    )
    soup = build_soup(html)
    parser = DayiDiseaseTemplateParser()
    classification = PageClassifier().classify(request, soup)

    match = parser.match(request, soup, extract_page_title(soup), classification)
    assert match is not None
    assert match.template_id == "dayi_disease_v1"

    result = parser.extract(request, soup, None)
    assert result.data["name"] == "气血不足"
    assert result.data["transmission"] == "无传染性"
    assert "归脾丸" in "".join(result.data["treatment"])


def test_dayi_qa_template_match_and_extract():
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="提取问答摘要",
    )
    soup = build_soup(html)
    parser = DayiQATemplateParser()
    classification = PageClassifier().classify(request, soup)

    match = parser.match(request, soup, extract_page_title(soup), classification)
    assert match is not None
    assert match.template_id == "dayi_qa_v1"

    result = parser.extract(request, soup, None)
    assert result.data["question"] == "气血不足怎么调理？"
    assert "规律作息" in result.data["summary"]
