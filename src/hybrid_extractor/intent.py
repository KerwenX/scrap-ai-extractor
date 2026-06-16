import re

from .config import DEFAULT_OUTPUT_PROMPT
from .models import ExtractionIntent


STOPWORDS = {
    "这是",
    "一个",
    "网页",
    "页面",
    "提取",
    "有关",
    "相关",
    "所有",
    "信息",
    "内容",
    "结构化",
}


def parse_intent(user_prompt: str) -> ExtractionIntent:
    normalized = user_prompt.strip() or DEFAULT_OUTPUT_PROMPT
    tokens = [
        token
        for token in re.split(r"[\s,，。；;、:：/]+", normalized)
        if token and token not in STOPWORDS
    ]
    return ExtractionIntent(
        entity_type=None,
        requested_capabilities=tokens[:12],
        normalized_prompt=normalized,
    )
