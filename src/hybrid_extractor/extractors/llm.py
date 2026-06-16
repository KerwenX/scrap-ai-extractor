from __future__ import annotations

import json

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
            extra_body={"thinking": {"type": "enabled" if settings.thinking_enabled else "disabled"}},
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
        normalized = self._normalize_result(result)
        return ExtractionResult(data=normalized)

    def _normalize_result(self, result) -> dict:
        if isinstance(result, dict):
            if len(result) == 1:
                only_value = next(iter(result.values()))
                decoded = self._try_decode_json_string(only_value)
                if decoded is not None:
                    return decoded
            return result

        decoded = self._try_decode_json_string(result)
        if decoded is not None:
            return decoded
        return {"result": result}

    def _try_decode_json_string(self, value) -> dict | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None
