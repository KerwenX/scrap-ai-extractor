from pathlib import Path

from hybrid_extractor.engine import HybridExtractionEngine
from hybrid_extractor.extractors.base import BaseFallbackExtractor
from hybrid_extractor.models import ExtractionIntent, ExtractionRequest, ExtractionResult


class FakeFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        return ExtractionResult(
            data={
                "name": "未知疾病",
                "summary": "这是回退结果",
                "symptoms": ["症状A"],
                "treatment": ["治疗A"],
                "result": "fallback"
            }
        )


def test_engine_uses_deterministic_parser_for_known_template():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/symptom/123.html",
        raw_html=html,
        user_prompt="提取疾病基本信息、病因、症状、治疗和预防",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_disease_v1"
    assert response.data["name"] == "气血不足"


def test_engine_falls_back_for_unknown_template():
    html = '<html><head><title>Unknown</title><meta name="description" content="fallback summary"></head><body><h1>Unknown Page</h1></body></html>'
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://example.com/1",
        raw_html=html,
        user_prompt="提取疾病基本信息、症状、治疗",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "llm"
    assert response.data["name"] == "未知疾病"
    candidate_path = response.debug_trace.get("template_candidate_path")
    assert candidate_path
    assert Path(candidate_path).exists()


def test_engine_uses_deterministic_parser_for_known_qa_template():
    html = Path("tests/fixtures/dayi_qa_sample.html").read_text(encoding="utf-8")
    engine = HybridExtractionEngine(fallback_extractor=FakeFallbackExtractor())
    request = ExtractionRequest(
        url="https://www.dayi.org.cn/qa/123.html",
        raw_html=html,
        user_prompt="提取问答摘要",
    )
    response = engine.extract(request)
    assert response.status == "success"
    assert response.extractor_type == "deterministic"
    assert response.template_id == "dayi_qa_v1"
    assert "规律作息" in response.data["summary"]
