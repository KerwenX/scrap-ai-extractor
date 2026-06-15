from __future__ import annotations

from scrapegraphai.graphs import DocumentScraperGraph
from scrapegraphai.models import DeepSeek

from ..config import load_app_settings
from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult
from ..prompts import PROMPT_VERSION, build_extraction_prompt
from .base import BaseFallbackExtractor


class ScrapeGraphFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        prompt = build_extraction_prompt(intent)
        settings = load_app_settings().llm

        if not settings.api_key:
            raise ValueError(
                "未配置 LLM API Key。请在 config/app_config.json 中填写 api_key，"
                "或设置环境变量 DEEPSEEK_API_KEY。"
            )

        model = DeepSeek(
            api_key=settings.api_key,
            model=settings.model,
            reasoning_effort=settings.reasoning_effort,
            model_kwargs={
                "extra_body": {"thinking": {"type": "enabled" if settings.thinking_enabled else "disabled"}}
            },
        )
        graph = DocumentScraperGraph(
            prompt=prompt,
            source=request.raw_html,
            config={
                "llm": {"model_instance": model, "model_tokens": settings.max_tokens},
                "metadata": {"prompt_version": PROMPT_VERSION},
            },
        )
        result = graph.run()
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        if not isinstance(result, dict):
            result = {"result": result}
        return ExtractionResult(data=result)
