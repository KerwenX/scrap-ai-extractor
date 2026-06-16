from pathlib import Path

from hybrid_extractor.classification import PageClassifier
from hybrid_extractor.models import ExtractionRequest
from hybrid_extractor.preprocessing import build_soup, extract_page_title
from hybrid_extractor.services.template_service import TemplateService
from hybrid_extractor.template_registry import TemplateRegistry


def test_dayi_disease_template_is_loaded_from_manifest_and_extracts():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息、病因、症状、诊断、治疗和预防",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(template_service=TemplateService())

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=None,
    )
    assert match is not None
    assert parser is not None
    assert match.template_id == "dayi_disease_v1"
    assert parser.parser_key == "generic:rule"

    result = parser.extract(request, soup, None)
    assert result.data["name"] == "气血不足"
    assert "神疲乏力" in result.data["symptoms"]
    assert "益气补血" in result.data["treatment"]


def test_dayi_qa_template_is_loaded_from_manifest_and_extracts():
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="提取问答摘要",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(template_service=TemplateService())

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=None,
    )
    assert match is not None
    assert parser is not None
    assert match.template_id == "dayi_qa_v1"
    assert parser.parser_key == "generic:rule"

    result = parser.extract(request, soup, None)
    assert "规律作息" in result.data["summary"]
    assert result.data["question"] == "气血不足怎么调理？"


def test_inactive_manifest_is_not_matched(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息",
    )
    builtin_manifest = TemplateService().get_manifest("dayi_disease_v1")
    assert builtin_manifest is not None
    service.upsert_manifest(builtin_manifest.model_copy(update={"active": False}))

    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(template_service=service)

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=None,
    )
    assert match is None
    assert parser is None


def test_archived_manifest_is_not_matched(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息",
    )
    builtin_manifest = TemplateService().get_manifest("dayi_disease_v1")
    assert builtin_manifest is not None
    service.upsert_manifest(
        builtin_manifest.model_copy(update={"active": False, "lifecycle_status": "archived"})
    )

    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(template_service=service)

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=None,
    )
    assert match is None
    assert parser is None
