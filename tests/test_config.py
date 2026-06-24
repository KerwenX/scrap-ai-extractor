import json

from hybrid_extractor import config as config_module


def test_load_app_settings_reads_local_file_and_env_override(monkeypatch, tmp_path):
    app_config_path = tmp_path / "app_config.json"
    app_config_path.write_text(
        json.dumps(
            {
                "llm": {
                    "api_key": "file-key",
                    "model": "file-model",
                    "reasoning_effort": "medium",
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_module, "APP_CONFIG_PATH", app_config_path)
    monkeypatch.setattr(
        config_module, "APP_CONFIG_TEMPLATE_PATH", tmp_path / "app_config.template.json"
    )
    config_module.load_app_settings.cache_clear()

    settings = config_module.load_app_settings()
    assert settings.llm.api_key == "file-key"
    assert settings.llm.model == "file-model"

    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    monkeypatch.setenv("SCRAPE_MODEL", "env-model")
    config_module.load_app_settings.cache_clear()

    settings = config_module.load_app_settings()
    assert settings.llm.api_key == "env-key"
    assert settings.llm.model == "env-model"


def test_load_app_settings_supports_generic_llm_provider_fields(monkeypatch, tmp_path):
    app_config_path = tmp_path / "app_config.json"
    app_config_path.write_text(
        json.dumps(
            {
                "llm": {
                    "provider": "deepseek",
                    "api_key": "file-key",
                    "base_url": "https://api.deepseek.com",
                    "model": "file-model",
                    "temperature": 0.3,
                    "stream": False,
                    "request_timeout_seconds": 90,
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_module, "APP_CONFIG_PATH", app_config_path)
    monkeypatch.setattr(
        config_module, "APP_CONFIG_TEMPLATE_PATH", tmp_path / "app_config.template.json"
    )
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "generic-key")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "glm47")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.1")
    monkeypatch.setenv("LLM_STREAM", "true")
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_SECONDS", "240")
    config_module.load_app_settings.cache_clear()

    settings = config_module.load_app_settings()
    assert settings.llm.provider == "openai_compatible"
    assert settings.llm.api_key == "generic-key"
    assert settings.llm.base_url == "http://127.0.0.1:8000/v1/chat/completions"
    assert settings.llm.model == "glm47"
    assert settings.llm.temperature == 0.1
    assert settings.llm.stream is True
    assert settings.llm.request_timeout_seconds == 240
