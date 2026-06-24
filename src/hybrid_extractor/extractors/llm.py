from __future__ import annotations

import json
from typing import Iterable

from ..config import LlmSettings, load_app_settings
from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult
from ..prompts import PROMPT_VERSION, build_extraction_prompt
from .base import BaseFallbackExtractor


class ScrapeGraphFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        prompt = build_extraction_prompt(intent)
        settings = load_app_settings().llm

        if not settings.api_key:
            raise ValueError(
                "未配置 LLM API Key。请在 config/app_config.json 中填写 llm.api_key，"
                "或设置环境变量 LLM_API_KEY。"
            )

        provider = self._normalize_provider(settings.provider)
        if provider == "deepseek":
            result = self._extract_with_scrapegraph_deepseek(prompt, request, settings)
        elif provider in {"openai_compatible", "openai-compatible", "glm", "openai"}:
            result = self._extract_with_openai_compatible(prompt, request, settings)
        else:
            raise ValueError(
                f"Unsupported llm.provider: {settings.provider}. "
                "Supported values: deepseek, openai_compatible."
            )

        normalized = self._normalize_result(result)
        return ExtractionResult(data=normalized)

    def _extract_with_scrapegraph_deepseek(
        self,
        prompt: str,
        request: ExtractionRequest,
        settings: LlmSettings,
    ):
        try:
            from scrapegraphai.graphs import DocumentScraperGraph
            from scrapegraphai.models import DeepSeek
        except ImportError as exc:
            raise RuntimeError(
                "DeepSeek provider requires scrapegraphai. Please install the dependency first."
            ) from exc

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
            return result.model_dump()
        return result

    def _extract_with_openai_compatible(
        self,
        prompt: str,
        request: ExtractionRequest,
        settings: LlmSettings,
    ):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI-compatible provider requires the openai package. "
                "Please install dependencies again."
            ) from exc

        client = OpenAI(
            api_key=settings.api_key,
            base_url=self._normalize_openai_base_url(settings.base_url),
            timeout=settings.request_timeout_seconds,
        )
        messages = self._build_openai_messages(prompt, request)
        request_kwargs = {
            "model": settings.model,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "stream": settings.stream,
        }
        response = client.chat.completions.create(**request_kwargs)
        if settings.stream:
            return self._read_streaming_content(response)
        return self._extract_response_content(response)

    def _build_openai_messages(self, prompt: str, request: ExtractionRequest) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "你是网页结构化抽取引擎。"
                    "只输出一个 JSON 对象，不要输出解释、Markdown、代码块或额外文本。"
                    "字段名优先遵循用户需求中的语言习惯。"
                    "无法可靠抽取的字段直接省略。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\n"
                    "以下是待解析的网页源码，请直接输出结构化 JSON：\n"
                    f"{request.raw_html}"
                ),
            },
        ]

    def _read_streaming_content(self, response: Iterable) -> str:
        chunks: list[str] = []
        for chunk in response:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue
            content = getattr(delta, "content", None)
            if content:
                chunks.append(content)
        return "".join(chunks).strip()

    def _extract_response_content(self, response) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        if message is None:
            return ""
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "".join(text_parts).strip()
        return str(content).strip()

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
        text = self._strip_code_fence(value.strip())
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None

    def _strip_code_fence(self, text: str) -> str:
        if not text.startswith("```"):
            return text
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            return "\n".join(lines[1:-1]).strip()
        return text

    def _normalize_provider(self, provider: str) -> str:
        return provider.strip().lower().replace(" ", "_")

    def _normalize_openai_base_url(self, base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")
        for suffix in ("/chat/completions",):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        return normalized
