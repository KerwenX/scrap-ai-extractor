from pathlib import Path

from hybrid_extractor.classification import PageClassifier
from hybrid_extractor.models import ExtractionRequest
from hybrid_extractor.preprocessing import build_soup


def test_classifier_detects_tabbed_detail_page():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    classifier = PageClassifier()
    result = classifier.classify(
        ExtractionRequest(
            url="https://www.dayi.org.cn/symptom/123.html",
            raw_html=html,
            user_prompt="提取疾病信息",
        ),
        build_soup(html),
    )
    assert result.site_id == "dayi.org.cn"
    assert result.scenario == "detail_tabbed"
    assert result.page_type == "detail_page"


def test_classifier_detects_qa_detail_page():
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    classifier = PageClassifier()
    result = classifier.classify(
        ExtractionRequest(
            url="https://www.dayi.org.cn/qa/123.html",
            raw_html=html,
            user_prompt="提取问答内容",
        ),
        build_soup(html),
    )
    assert result.site_id == "dayi.org.cn"
    assert result.scenario == "qa_detail"
    assert result.page_type == "qa_page"
