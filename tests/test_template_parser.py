from pathlib import Path

from hybrid_extractor.classification import PageClassifier
from hybrid_extractor.models import (
    ExtractionPlan,
    ExtractionRequest,
    FieldRule,
    FieldSelectorRule,
    PageFingerprint,
    TemplateManifest,
)
from hybrid_extractor.fingerprinting import build_fingerprint
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


def test_registry_prefers_template_with_higher_runtime_hit_rate(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <body>
        <div class="header"><h1>Paper A</h1></div>
        <table class="info-table">
          <tr><td>作者</td><td>张三</td></tr>
          <tr><td>期刊</td><td>经济研究</td></tr>
        </table>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://example.com/article/1",
        raw_html=html,
        user_prompt="提取论文信息",
    )
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    service.upsert_manifest(
        TemplateManifest(
            template_id="paper_template_low_v1",
            parser_key="generic:rule",
            site_id="example.com",
            site_name="example.com",
            page_type="article_page",
            scenario="article_detail",
            version="v1",
            template_key="paper_template_low",
            lifecycle_status="active",
            active=True,
            fingerprint=PageFingerprint(
                dom_signature=fingerprint.dom_signature,
                headings=["Completely Different"],
                key_ids=[],
                key_classes=[],
            ),
            required_fields=["title", "作者", "期刊"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                    FieldRule(field_name="作者", selectors=[FieldSelectorRule(kind="label_value", value="作者")]),
                    FieldRule(field_name="期刊", selectors=[FieldSelectorRule(kind="label_value", value="期刊")]),
                ]
            ),
        )
    )
    service.upsert_manifest(
        TemplateManifest(
            template_id="paper_template_high_fp_v1",
            parser_key="generic:rule",
            site_id="example.com",
            site_name="example.com",
            page_type="article_page",
            scenario="article_detail",
            version="v1",
            template_key="paper_template_high_fp",
            lifecycle_status="active",
            active=True,
            fingerprint=fingerprint,
            required_fields=["title", "作者", "期刊"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value=".missing-title")]),
                    FieldRule(field_name="作者", selectors=[FieldSelectorRule(kind="label_value", value="不存在")]),
                    FieldRule(field_name="期刊", selectors=[FieldSelectorRule(kind="label_value", value="期刊")]),
                ]
            ),
        )
    )
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(template_service=service)

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=fingerprint,
    )

    assert match is not None
    assert parser is not None
    assert match.template_id == "paper_template_low_v1"
    assert match.selector_hit_rate == 1.0
    assert match.required_hit_rate == 1.0
    assert match.score_breakdown["fingerprint_score"] < 1.0


def test_registry_allows_same_site_template_reuse_with_scenario_mismatch_when_runtime_score_is_strong(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <body>
        <h1>Doctor A</h1>
        <table>
          <tr><td>医院</td><td>示例医院</td></tr>
        </table>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://example.com/doctor/1",
        raw_html=html,
        user_prompt="提取医生信息",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    fingerprint = build_fingerprint(soup)
    service.upsert_manifest(
        TemplateManifest(
            template_id="doctor_family_v1",
            parser_key="generic:rule",
            site_id="example.com",
            site_name="example.com",
            page_type="article_page",
            scenario="article_detail",
            version="v1",
            template_key="doctor_family",
            lifecycle_status="active",
            active=True,
            fingerprint=fingerprint,
            required_fields=["姓名", "医院"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="姓名", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                    FieldRule(field_name="医院", selectors=[FieldSelectorRule(kind="label_value", value="医院")]),
                ]
            ),
        )
    )
    registry = TemplateRegistry(template_service=service)

    match, parser = registry.match(
        request,
        soup,
        extract_page_title(soup),
        classification,
        fingerprint=fingerprint,
    )

    assert classification.scenario == "detail_page"
    assert match is not None
    assert parser is not None
    assert match.template_id == "doctor_family_v1"
    assert match.required_hit_rate == 1.0
    assert 0 < match.classification_affinity < 1.0
