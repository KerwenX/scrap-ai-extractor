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
