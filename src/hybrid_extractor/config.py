from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATE_DIR = CONFIG_DIR / "templates"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_STORE_DIR = DATA_DIR / "template_store"
TEMPLATE_CANDIDATE_DIR = DATA_DIR / "template_candidates"
LOG_DIR = PROJECT_ROOT / "logs"
APP_CONFIG_PATH = CONFIG_DIR / "app_config.json"
APP_CONFIG_TEMPLATE_PATH = CONFIG_DIR / "app_config.template.json"

DEFAULT_OUTPUT_PROMPT = "提取页面中与用户需求最相关的结构化信息，并尽量输出中文。"
DEFAULT_MEDICAL_PROMPT = "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防。"


class LlmSettings(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"
    reasoning_effort: str = "high"
    thinking_enabled: bool = True
    max_tokens: int = 128000


class AppSettings(BaseModel):
    llm: LlmSettings = Field(default_factory=LlmSettings)


def ensure_app_config_template() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if APP_CONFIG_TEMPLATE_PATH.exists():
        return
    APP_CONFIG_TEMPLATE_PATH.write_text(
        AppSettings().model_dump_json(indent=2),
        encoding="utf-8",
    )


@lru_cache(maxsize=1)
def load_app_settings() -> AppSettings:
    ensure_app_config_template()
    payload = {}

    if APP_CONFIG_PATH.exists():
        payload = json.loads(APP_CONFIG_PATH.read_text(encoding="utf-8"))

    settings = AppSettings.model_validate(payload)
    llm = settings.llm.model_copy(
        update={
            "api_key": os.getenv("DEEPSEEK_API_KEY", settings.llm.api_key),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", settings.llm.base_url),
            "model": os.getenv("SCRAPE_MODEL", settings.llm.model),
            "reasoning_effort": os.getenv(
                "DEEPSEEK_REASONING_EFFORT", settings.llm.reasoning_effort
            ),
        }
    )
    return settings.model_copy(update={"llm": llm})
