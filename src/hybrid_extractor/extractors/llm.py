from __future__ import annotations

import os

from scrapegraphai.graphs import DocumentScraperGraph
from scrapegraphai.models import DeepSeek

from ..config import DEFAULT_DEEPSEEK_API_KEY
from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult
from ..prompts import PROMPT_VERSION, build_extraction_prompt
from .base import BaseFallbackExtractor


class ScrapeGraphFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        prompt = build_extraction_prompt(intent)

        model = DeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY") or DEFAULT_DEEPSEEK_API_KEY,
            model=os.getenv("SCRAPE_MODEL", "deepseek-v4-pro"),
            reasoning_effort=os.getenv("DEEPSEEK_REASONING_EFFORT", "high"),
            model_kwargs={"extra_body": {"thinking": {"type": "enabled"}}},
        )
        graph = DocumentScraperGraph(
            prompt=prompt,
            source=request.raw_html,
            config={
                "llm": {"model_instance": model, "model_tokens": 128000},
                "metadata": {"prompt_version": PROMPT_VERSION},
            },
        )
        result = graph.run()
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        if not isinstance(result, dict):
            result = {"result": result}
        return ExtractionResult(data=result)
