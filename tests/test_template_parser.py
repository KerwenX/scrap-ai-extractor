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
from hybrid_extractor.config import TEMPLATE_DIR
from hybrid_extractor.services.template_service import TemplateService
from hybrid_extractor.template_registry import TemplateRegistry


def test_dayi_disease_template_is_loaded_from_manifest_and_extracts(tmp_path):
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息、病因、症状、诊断、治疗和预防",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(
        template_service=TemplateService(
            template_dir=TEMPLATE_DIR,
            template_store_dir=tmp_path / "template_store",
            template_candidate_dir=tmp_path / "template_candidates",
            include_builtin_templates=True,
        )
    )

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


def test_dayi_qa_template_is_loaded_from_manifest_and_extracts(tmp_path):
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="提取问答摘要",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    registry = TemplateRegistry(
        template_service=TemplateService(
            template_dir=TEMPLATE_DIR,
            template_store_dir=tmp_path / "template_store",
            template_candidate_dir=tmp_path / "template_candidates",
            include_builtin_templates=True,
        )
    )

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
    builtin_manifest = TemplateService(include_builtin_templates=True).get_manifest("dayi_disease_v1")
    assert builtin_manifest is not None
    service.upsert_manifest(
        builtin_manifest.model_copy(update={"active": False, "lifecycle_status": "deprecated"})
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
    builtin_manifest = TemplateService(include_builtin_templates=True).get_manifest("dayi_disease_v1")
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


def test_registry_reuses_same_domain_family_template_across_subdomains(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <head>
        <meta name="description" content="OTC是非处方药。" />
      </head>
      <body>
        <h1>OTC</h1>
        <div id="name"><span>OTC</span></div>
        <div id="appDisciplines"><span>药学</span></div>
        <div id="_intro">OTC是非处方药。</div>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/term/1143519",
        raw_html=html,
        user_prompt="提取词条信息",
    )
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    classification = PageClassifier().classify(request, soup)
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
    assert match.template_id == "term_family_v1"
    assert match.score_breakdown["site_affinity"] == 0.85


def test_registry_prioritizes_same_url_pattern_before_other_site_templates(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <body>
        <h1>词条页面</h1>
        <div id="name">词条页面</div>
        <div id="_intro">页面概念</div>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://m.dayi.org.cn/term/800536",
        raw_html=html,
        user_prompt="提取词条信息",
    )
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    classification = PageClassifier().classify(request, soup)
    term_hash = service.build_url_pattern_hash_for_url(request.url)
    doctor_hash = service.build_url_pattern_hash_for_url("https://m.dayi.org.cn/doctor/1150764")
    service.upsert_manifest(
        TemplateManifest(
            template_id="doctor_family_v1",
            parser_key="generic:rule",
            site_id="m.dayi.org.cn",
            site_name="m.dayi.org.cn",
            page_type="article_page",
            scenario="article_detail",
            version="v1",
            template_key="doctor_family",
            url_pattern_hash=doctor_hash,
            lifecycle_status="active",
            active=True,
            fingerprint=fingerprint,
            required_fields=["标题"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="标题", selectors=[FieldSelectorRule(kind="css", value=".missing")]),
                ]
            ),
        )
    )
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
            url_pattern_hash=term_hash,
            lifecycle_status="active",
            active=True,
            fingerprint=fingerprint,
            required_fields=["标题"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="标题", selectors=[FieldSelectorRule(kind="css", value="h1")]),
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

    assert match is not None
    assert parser is not None
    assert match.template_id == "term_family_v1"
    assert match.score_breakdown["url_pattern_affinity"] == 1.0


def test_registry_rejects_low_fingerprint_low_affinity_false_positive(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <head>
        <meta name="description" content="OTC是非处方药。" />
      </head>
      <body>
        <h1>OTC</h1>
        <div class="summary">OTC是非处方药。</div>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/term/1143519",
        raw_html=html,
        user_prompt="提取词条信息",
    )
    soup = build_soup(html)
    fingerprint = build_fingerprint(soup)
    classification = PageClassifier().classify(request, soup)
    service.upsert_manifest(
        TemplateManifest(
            template_id="qa_family_v1",
            parser_key="generic:rule",
            site_id="dayi.org.cn",
            site_name="dayi.org.cn",
            page_type="qa_page",
            scenario="qa_detail",
            version="v1",
            template_key="qa_family",
            lifecycle_status="active",
            active=True,
            fingerprint=PageFingerprint(
                dom_signature="1111222233334444",
                headings=["Completely Different"],
                key_ids=[],
                key_classes=[],
            ),
            required_fields=["question", "summary"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="question", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                    FieldRule(field_name="summary", selectors=[FieldSelectorRule(kind="meta", value="description")]),
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

    assert match is None
    assert parser is None


def test_registry_rejects_no_fingerprint_low_affinity_partial_false_positive(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    html = """
    <html>
      <head>
        <meta name="description" content="OTC是非处方药。" />
      </head>
      <body>
        <h1>OTC</h1>
      </body>
    </html>
    """
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/term/1143519",
        raw_html=html,
        user_prompt="提取词条信息",
    )
    soup = build_soup(html)
    classification = PageClassifier().classify(request, soup)
    service.upsert_manifest(
        TemplateManifest(
            template_id="qa_family_v1",
            parser_key="generic:rule",
            site_id="dayi.org.cn",
            site_name="dayi.org.cn",
            page_type="qa_page",
            scenario="qa_detail",
            version="v1",
            template_key="qa_family",
            lifecycle_status="active",
            active=True,
            required_fields=["summary"],
            extraction_plan=ExtractionPlan(
                fields=[
                    FieldRule(field_name="question", selectors=[FieldSelectorRule(kind="css", value="h1")]),
                    FieldRule(field_name="summary", selectors=[FieldSelectorRule(kind="meta", value="description")]),
                    FieldRule(field_name="doctor_name", selectors=[FieldSelectorRule(kind="css", value=".doctor-name")]),
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
        fingerprint=None,
    )

    assert match is None
    assert parser is None


def test_manifest_is_stored_under_site_subdirectory_and_can_be_loaded(tmp_path):
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
        template_key="doctor_family",
        lifecycle_status="active",
        active=True,
        required_fields=["标题"],
        extraction_plan=ExtractionPlan(
            fields=[FieldRule(field_name="标题", selectors=[FieldSelectorRule(kind="css", value="h1")])]
        ),
    )

    path = service.upsert_manifest(manifest)

    assert path == tmp_path / "template_store" / "m_dayi_org_cn" / "doctor_family_v1.json"
    loaded = service.get_manifest("doctor_family_v1")
    assert loaded is not None
    assert loaded.site_id == "m.dayi.org.cn"


def test_delete_manifest_supports_nested_site_directory(tmp_path):
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    manifest = TemplateManifest(
        template_id="paper_family_v1",
        parser_key="generic:rule",
        site_id="erj.ajcass.com",
        site_name="erj.ajcass.com",
        page_type="detail_page",
        scenario="detail_page",
        version="v1",
        template_key="paper_family",
        lifecycle_status="active",
        active=True,
        required_fields=["标题"],
        extraction_plan=ExtractionPlan(
            fields=[FieldRule(field_name="标题", selectors=[FieldSelectorRule(kind="css", value="h1")])]
        ),
    )

    path = service.upsert_manifest(manifest)
    assert path.exists()

    deleted = service.delete_manifest("paper_family_v1")

    assert deleted is True
    assert not path.exists()
    assert service.get_manifest("paper_family_v1") is None
