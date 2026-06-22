from pathlib import Path

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
    TemplateManifest,
)
from hybrid_extractor.preprocessing import build_soup
from hybrid_extractor.config import TEMPLATE_DIR
from hybrid_extractor.services.template_service import TemplateService


class FakeFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "name": "Unknown Disease",
                "summary": "Fallback summary",
                "symptoms": ["Symptom A"],
                "treatment": ["Treatment A"],
                "result": "fallback",
            }
        )


class GenericFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "title": "Paper Title",
                "content": "Generic extracted content",
            }
        )


class SolidifyingFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "name": "Custom Disease",
                "summary": "Page summary",
                "causes": "Cause content",
                "symptoms": "Symptom content",
                "diagnosis": "Diagnosis content",
                "treatment": "Treatment content",
            }
        )


class WrappedObjectFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "content": {
                    "name": "Miao Yang",
                    "department": "Cardiology",
                    "practice_location": "Xiyuan Hospital",
                }
            }
        )


class WrappedDoctorFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "content": {
                    "姓名": "苏惠萍",
                    "简介": "苏惠萍，主任医师。",
                }
            }
        )


def test_engine_uses_deterministic_parser_for_known_template(tmp_path):
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    service = TemplateService(
        template_dir=TEMPLATE_DIR,
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
        include_builtin_templates=True,
    )
    engine = HybridExtractionEngine(
        fallback_extractor=FakeFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="Extract disease information, causes, symptoms, treatment and prevention",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_disease_v1"
    assert response.data["name"] == "气血不足"


def test_engine_falls_back_for_unknown_template(tmp_path):
    html = (
        '<html><head><title>Unknown</title><meta name="description" content="fallback summary">'
        "</head><body><h1>Unknown Page</h1></body></html>"
    )
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
        include_builtin_templates=False,
    )
    engine = HybridExtractionEngine(
        fallback_extractor=FakeFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/1",
        raw_html=html,
        user_prompt="Extract disease information, symptoms and treatment",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.data["name"] == "Unknown Disease"
    assert response.debug_trace["prompt_version"] == "v1"
    assert response.debug_trace["template_analysis"]["summary"]
    assert response.debug_trace["template_analysis_prompt"]
    assert response.debug_trace["template_plan_prompt"]
    candidate_path = response.debug_trace.get("template_candidate_path")
    assert candidate_path
    assert Path(candidate_path).exists()
    candidate_payload = Path(candidate_path).read_text(encoding="utf-8")
    assert '"analysis"' in candidate_payload
    assert '"proposed_plan"' in candidate_payload


def test_engine_auto_solidifies_and_reuses_manifest(tmp_path):
    html = """
    <html>
      <head>
        <title>Custom Disease Page</title>
        <meta name="description" content="Page summary">
      </head>
      <body>
        <h1>Custom Disease</h1>
        <div class="van-tabs__nav">
          <div role="tab"><span class="van-tab__text">Causes</span></div>
          <div role="tab"><span class="van-tab__text">Symptoms</span></div>
          <div role="tab"><span class="van-tab__text">Diagnosis</span></div>
          <div role="tab"><span class="van-tab__text">Treatment</span></div>
        </div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">Cause content</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">Symptom content</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">Diagnosis content</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">Treatment content</div></div>
      </body>
    </html>
    """
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    engine = HybridExtractionEngine(
        fallback_extractor=SolidifyingFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/custom-disease",
        raw_html=html,
        user_prompt="Extract disease information, causes, symptoms, diagnosis and treatment",
    )

    first_response = engine.extract(request)
    assert first_response.status == "success"
    assert first_response.extractor_type == "llm"
    assert first_response.debug_trace["solidified_template_id"]

    second_response = engine.extract(request)
    assert second_response.status == "success"
    assert second_response.extractor_type == "deterministic"
    assert second_response.template_id == first_response.debug_trace["solidified_template_id"]
    assert second_response.data["name"] == "Custom Disease"
    assert second_response.data["symptoms"] == "Symptom content"
    assert second_response.data["treatment"] == "Treatment content"


def test_engine_uses_deterministic_parser_for_known_qa_template(tmp_path):
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    service = TemplateService(
        template_dir=TEMPLATE_DIR,
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
        include_builtin_templates=True,
    )
    engine = HybridExtractionEngine(
        fallback_extractor=FakeFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="Extract the Q&A summary",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_qa_v1"
    assert "规律作息" in response.data["summary"]


def test_engine_allows_generic_unknown_page_without_fixed_required_fields(tmp_path):
    html = "<html><head><title>Article</title></head><body><h1>Paper</h1></body></html>"
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
        include_builtin_templates=False,
    )
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/article/1",
        raw_html=html,
        user_prompt="This is a paper page, extract all page information",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.data["title"] == "Paper Title"


def test_engine_keeps_dsl_result_when_fingerprint_similarity_is_low_but_validation_passes(tmp_path):
    html = "<html><head><title>Article</title></head><body><h1>Paper</h1><div id='content'>Body</div></body></html>"
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    manifest = TemplateManifest(
        template_id="example_article_v1",
        parser_key="generic:rule",
        site_id="example.com",
        site_name="example.com",
        page_type="detail_page",
        scenario="detail_page",
        version="v1",
        template_key="example_article",
        lifecycle_status="active",
        active=True,
        fingerprint=PageFingerprint(
            dom_signature=fingerprint.dom_signature,
            headings=[
                "Different Heading One",
                "Different Heading Two",
                "Different Heading Three",
                "Different Heading Four",
                "Paper",
            ],
            key_ids=["content"],
            key_classes=[],
        ),
        required_fields=["title"],
        extraction_plan=ExtractionPlan(
            fields=[FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value="h1")])]
        ),
    )
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    service.upsert_manifest(manifest)
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/article/1",
        raw_html=html,
        user_prompt="extract title",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.drift_detected is False
    assert response.debug_trace["drift_report"]["reason"] == "stable_valid_dsl"
    assert response.data["title"] == "Paper"


def test_engine_unwraps_generic_content_object_for_candidate_plan(tmp_path):
    html = """
    <html>
      <body>
        <h1>Miao Yang</h1>
        <div id="department">Cardiology</div>
        <div id="hospital">Xiyuan Hospital</div>
      </body>
    </html>
    """
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    engine = HybridExtractionEngine(
        fallback_extractor=WrappedObjectFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://m.dayi.org.cn/doctor/1125751",
        raw_html=html,
        user_prompt="Extract doctor name, department and practice location",
    )
    response = engine.extract(request)
    assert response.status == "success"
    candidate_path = Path(response.debug_trace["template_candidate_path"])
    candidate_payload = candidate_path.read_text(encoding="utf-8")
    assert '"name"' in candidate_payload
    assert '"department"' in candidate_payload
    assert '"proposed_plan"' in candidate_payload


def test_engine_reuses_dsl_template_with_low_fingerprint_when_validation_passes(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    manifest = TemplateManifest(
        template_id="doctor_family_v1",
        parser_key="generic:rule",
        site_id="m.dayi.org.cn",
        site_name="m.dayi.org.cn",
        page_type="article_page",
        scenario="article_detail",
        version="v1",
        template_key="m_dayi_org_cn_article_detail_article_page_0403cf10",
        lifecycle_status="active",
        active=True,
        fingerprint=PageFingerprint(
            dom_signature="1111222233334444",
            headings=["Another page"],
            key_ids=["_intro"],
            key_classes=["item-content"],
        ),
        required_fields=["姓名", "简介"],
        extraction_plan=ExtractionPlan(
            fields=[
                FieldRule(field_name="姓名", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                FieldRule(field_name="简介", selectors=[FieldSelectorRule(kind="id", value="_intro")]),
            ]
        ),
    )
    service.upsert_manifest(manifest)
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://m.dayi.org.cn/doctor/1150764",
        raw_html="""
        <html>
          <head><title>Doctor Detail</title><meta name="description" content="Su Huiping, chief physician."></head>
          <body>
            <h1>Su Huiping</h1>
            <div id="_intro">Su Huiping, chief physician.</div>
          </body>
        </html>
        """,
        user_prompt="Extract doctor name and profile",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "doctor_family_v1"
    assert response.data["姓名"] == "Su Huiping"
    assert response.data["简介"] == "Su Huiping, chief physician."
    assert response.debug_trace["drift_report"]["reason"] in {"stable_valid_dsl", "fingerprint_similarity_low_but_valid_dsl"}


def test_engine_preserves_dsl_plan_when_backfilling_missing_fingerprint(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    manifest = TemplateManifest(
        template_id="paper_family_v1",
        parser_key="generic:rule",
        site_id="example.com",
        site_name="example.com",
        page_type="article_page",
        scenario="article_detail",
        version="v1",
        template_key="paper_family",
        lifecycle_status="active",
        active=True,
        required_fields=["title", "author"],
        extraction_plan=ExtractionPlan(
            fields=[
                FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                FieldRule(field_name="author", selectors=[FieldSelectorRule(kind="label_value", value="作者")]),
            ]
        ),
    )
    service.upsert_manifest(manifest)
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/paper/1",
        raw_html="""
        <html>
          <body>
            <h1>Paper One</h1>
            <table><tr><td>作者</td><td>Alice</td></tr></table>
          </body>
        </html>
        """,
        user_prompt="extract paper info",
    )

    first_response = engine.extract(request)
    second_response = engine.extract(
        request.model_copy(
            update={
                "raw_html": """
                <html>
                  <body>
                    <h1>Paper Two</h1>
                    <table><tr><td>作者</td><td>Bob</td></tr></table>
                  </body>
                </html>
                """
            }
        )
    )

    stored_manifest = service.get_manifest("paper_family_v1")
    assert first_response.extractor_type == "deterministic"
    assert second_response.extractor_type == "deterministic"
    assert second_response.data["title"] == "Paper Two"
    assert second_response.data["author"] == "Bob"
    assert stored_manifest is not None
    assert stored_manifest.extraction_plan is not None
    assert len(stored_manifest.extraction_plan.fields) == 2


def test_engine_validates_unwrapped_llm_content_payload(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    manifest = TemplateManifest(
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
        required_fields=["姓名", "简介"],
    )
    service.upsert_manifest(manifest)
    engine = HybridExtractionEngine(
        fallback_extractor=WrappedDoctorFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/doctor/1",
        raw_html="<html><body><h1>Doctor</h1></body></html>",
        user_prompt="extract doctor info",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.data["姓名"] == "苏惠萍"
    assert response.data["简介"] == "苏惠萍，主任医师。"
    assert response.validation_report.passed is True
def test_template_only_mode_allows_empty_url_and_scans_all_templates(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    service.upsert_manifest(
        TemplateManifest(
            template_id="paper_family_v1",
            parser_key="generic:rule",
            site_id="example.com",
            site_name="example.com",
            page_type="detail_page",
            scenario="detail_page",
            version="v1",
            template_key="paper_family_deadbeef_feedface",
            lifecycle_status="active",
            active=True,
            required_fields=["title", "abstract"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value=".content-right .title")]),
                    FieldRule(field_name="abstract", selectors=[FieldSelectorRule(kind="css", value=".content-right .message")]),
                ]
            ),
        )
    )
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="",
        raw_html="""
        <html>
          <head><title>Journal</title></head>
          <body>
            <div class="content-right">
              <div class="title">Paper</div>
              <div class="message">Abstract text</div>
            </div>
          </body>
        </html>
        """,
        user_prompt="extract title",
        run_mode="template_only",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "paper_family_v1"


def test_template_only_mode_never_falls_back_to_llm(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/no-template",
        raw_html="<html><body><h1>Paper</h1></body></html>",
        user_prompt="extract title",
        run_mode="template_only",
    )

    response = engine.extract(request)
    assert response.status == "failed"
    assert response.extractor_type == "none"
    assert response.data == {}
    assert response.debug_trace["template_only_failure"]["reason"] == "no_matching_active_template"


def test_engine_does_not_upgrade_existing_template_when_no_template_was_matched(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    existing = TemplateManifest(
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
        required_fields=["title"],
        extraction_plan=ExtractionPlan(
            fields=[FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value=".missing")])]
        ),
    )
    service.upsert_manifest(existing)

    class RichFallbackExtractor(BaseFallbackExtractor):
        def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
            return ExtractionResult(
                data={
                    "title": "Paper One",
                    "abstract": "Abstract text",
                    "author": "Alice",
                }
            )

    engine = HybridExtractionEngine(
        fallback_extractor=RichFallbackExtractor(),
        template_service=service,
    )
    response = engine.extract(
        ExtractionRequest(
            url="",
            raw_html="""
            <html>
              <head><title>Journal</title></head>
              <body>
                <div class="content-right">
                  <div class="title">Paper One</div>
                  <div class="message">【作者】 Alice 【内容提要】 Abstract text</div>
                </div>
              </body>
            </html>
            """,
            user_prompt="extract paper info",
        )
    )

    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.debug_trace["solidified_template_id"] != "paper_family_v2"
    assert service.get_manifest("paper_family_v1").active is True


def test_engine_reuses_same_domain_family_template_across_subdomains(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <head><meta name="description" content="OTC是非处方药。"></head>
      <body>
        <h1>OTC</h1>
        <div id="name">OTC</div>
        <div id="appDisciplines">药学</div>
        <div id="_intro">OTC是非处方药。</div>
      </body>
    </html>
    """
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    service.upsert_manifest(
        TemplateManifest(
            template_id="term_family_v1",
            parser_key="generic:rule",
            site_id="m.dayi.org.cn",
            site_name="m.dayi.org.cn",
            page_type="article_page",
            scenario="article_detail",
            version="v1",
            template_key="term_family",
            lifecycle_status="active",
            active=True,
            fingerprint=fingerprint,
            required_fields=["标题", "名称", "应用学科", "概念"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="标题", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                    FieldRule(field_name="名称", selectors=[FieldSelectorRule(kind="id", value="name")]),
                    FieldRule(field_name="应用学科", selectors=[FieldSelectorRule(kind="id", value="appDisciplines")]),
                    FieldRule(field_name="概念", selectors=[FieldSelectorRule(kind="id", value="_intro")]),
                ]
            ),
        )
    )
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/term/1143519",
        raw_html=html,
        user_prompt="提取词条信息",
    )

    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "term_family_v1"
    assert response.data["标题"] == "OTC"
    assert response.debug_trace["template_match"]["score_breakdown"]["site_affinity"] == 0.85


def test_engine_auto_solidifies_structural_template_and_reuses_across_same_layout(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    engine = HybridExtractionEngine(
        fallback_extractor=GenericFallbackExtractor(),
        template_service=service,
    )
    first_html = """
    <html>
      <body>
        <h1>OTC</h1>
        <div class="item-container">
          <div class="item-title-container">名称</div><span class="item-content">OTC</span>
        </div>
        <div class="item-container">
          <div class="item-title-container">英文名称</div><span class="item-content">over-the-counter drug</span>
        </div>
        <div class="public-container">
          <div class="title-line"><p>概念</p></div>
          <div class="item-content">OTC即非处方药。</div>
        </div>
      </body>
    </html>
    """
    second_html = """
    <html>
      <body>
        <h1>气</h1>
        <div class="item-container">
          <div class="item-title-container">名称</div><span class="item-content">气</span>
        </div>
        <div class="item-container">
          <div class="item-title-container">应用学科</div><span class="item-content">中医学</span>
        </div>
        <div class="public-container">
          <div class="title-line"><p>概念</p></div>
          <div class="item-content">气是生命活动基本物质。</div>
        </div>
        <div class="public-container">
          <div class="title-line"><p>分类</p></div>
          <div class="item-content">可分为元气、宗气、营气、卫气。</div>
        </div>
      </body>
    </html>
    """

    first_response = engine.extract(
        ExtractionRequest(
            url="https://www.dayi.org.cn/term/1143519",
            raw_html=first_html,
            user_prompt="提取词条信息",
        )
    )
    assert first_response.status == "success"
    assert first_response.extractor_type == "llm"
    assert first_response.debug_trace["solidified_template_id"]

    second_response = engine.extract(
        ExtractionRequest(
            url="https://www.dayi.org.cn/term/800536",
            raw_html=second_html,
            user_prompt="提取词条信息",
        )
    )
    assert second_response.status == "success"
    assert second_response.extractor_type == "deterministic"
    assert second_response.template_id == first_response.debug_trace["solidified_template_id"]
    assert second_response.data["标题"] == "气"
    assert second_response.data["名称"] == "气"
    assert second_response.data["应用学科"] == "中医学"
    assert second_response.data["概念"] == "气是生命活动基本物质。"
    assert second_response.data["分类"] == "可分为元气、宗气、营气、卫气。"
