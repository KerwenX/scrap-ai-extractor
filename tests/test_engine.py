from pathlib import Path

from hybrid_extractor.engine import HybridExtractionEngine
from hybrid_extractor.extractors.base import BaseFallbackExtractor
from hybrid_extractor.services.template_service import TemplateService
from hybrid_extractor.models import ExtractionIntent, ExtractionRequest, ExtractionResult


class FakeFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "name": "\u672a\u77e5\u75be\u75c5",
                "summary": "\u8fd9\u662f\u56de\u9000\u7ed3\u679c",
                "symptoms": ["\u75c7\u72b6A"],
                "treatment": ["\u6cbb\u7597A"],
                "result": "fallback",
            }
        )


def test_engine_uses_deterministic_parser_for_known_template():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="\u63d0\u53d6\u75be\u75c5\u57fa\u672c\u4fe1\u606f\u3001\u75c5\u56e0\u3001\u75c7\u72b6\u3001\u6cbb\u7597\u548c\u9884\u9632",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_disease_v1"
    assert response.data["name"] == "\u6c14\u8840\u4e0d\u8db3"


def test_engine_falls_back_for_unknown_template():
    html = (
        '<html><head><title>Unknown</title><meta name="description" content="fallback summary">'
        '</head><body><h1>Unknown Page</h1></body></html>'
    )
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://example.com/1",
        raw_html=html,
        user_prompt="\u63d0\u53d6\u75be\u75c5\u57fa\u672c\u4fe1\u606f\u3001\u75c7\u72b6\u3001\u6cbb\u7597",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.data["name"] == "\u672a\u77e5\u75be\u75c5"
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
        <meta name="description" content="这是页面摘要">
      </head>
      <body>
        <h1>自定义病名</h1>
        <div class="van-tabs__nav">
          <div role="tab"><span class="van-tab__text">病因</span></div>
          <div role="tab"><span class="van-tab__text">症状</span></div>
          <div role="tab"><span class="van-tab__text">诊断</span></div>
          <div role="tab"><span class="van-tab__text">治疗</span></div>
        </div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">病因内容</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">症状内容</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">诊断内容</div></div>
        <div class="van-tab__pane-wrapper"><div class="van-tab__pane">治疗内容</div></div>
      </body>
    </html>
    """
    service = TemplateService(
        template_dir=tmp_path / "templates",
        template_store_dir=tmp_path / "template_store",
        template_candidate_dir=tmp_path / "template_candidates",
    )
    engine = HybridExtractionEngine(
        fallback_extractor=FakeFallbackExtractor(),
        template_service=service,
    )
    request = ExtractionRequest(
        url="https://example.com/custom-disease",
        raw_html=html,
        user_prompt="提取疾病基本信息、病因、症状、诊断、治疗",
    )

    first_response = engine.extract(request)
    assert first_response.status == "success"
    assert first_response.extractor_type == "llm"
    assert first_response.debug_trace["solidified_template_id"]

    second_response = engine.extract(request)
    assert second_response.status == "success"
    assert second_response.extractor_type == "deterministic"
    assert second_response.template_id == first_response.debug_trace["solidified_template_id"]
    assert second_response.data["name"] == "自定义病名"
    assert second_response.data["symptoms"] == "症状内容"
    assert second_response.data["treatment"] == "治疗内容"


def test_engine_uses_deterministic_parser_for_known_qa_template():
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="\u63d0\u53d6\u95ee\u7b54\u6458\u8981",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_qa_v1"
    assert "\u89c4\u5f8b\u4f5c\u606f" in response.data["summary"]
