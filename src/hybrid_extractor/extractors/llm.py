from __future__ import annotations

import os

from scrapegraphai.graphs import DocumentScraperGraph
from scrapegraphai.models import DeepSeek

from ..config import DEFAULT_DEEPSEEK_API_KEY
from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult
from .base import BaseFallbackExtractor


class ScrapeGraphFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        prompt = f"""
你是网页结构化数据抽取系统。

用户需求：
{intent.normalized_prompt}

请根据页面内容抽取结构化信息，并返回 JSON 对象。要求：
1. 尽量只输出页面中明确出现的信息。
2. 如果页面看起来是疾病详情页，请尽量输出字段：
   name, summary, aliases, susceptible_population, transmission, departments,
   causes, symptoms, diagnosis, treatment, nursing_and_precautions, prevention, sections
3. 输出内容使用中文。
"""

        model = DeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY") or DEFAULT_DEEPSEEK_API_KEY,
            model=os.getenv("SCRAPE_MODEL", "deepseek-v4-pro"),
            reasoning_effort=os.getenv("DEEPSEEK_REASONING_EFFORT", "high"),
            model_kwargs={"extra_body": {"thinking": {"type": "enabled"}}},
        )
        graph = DocumentScraperGraph(
            prompt=prompt,
            source=request.raw_html,
            config={"llm": {"model_instance": model, "model_tokens": 128000}},
        )
        result = graph.run()
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        if not isinstance(result, dict):
            result = {"result": result}
        return ExtractionResult(data=result)
