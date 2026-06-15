from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATE_DIR = CONFIG_DIR / "templates"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_STORE_DIR = DATA_DIR / "template_store"
TEMPLATE_CANDIDATE_DIR = DATA_DIR / "template_candidates"
LOG_DIR = PROJECT_ROOT / "logs"

DEFAULT_OUTPUT_PROMPT = (
    "提取页面中与用户需求最相关的结构化信息，并尽量输出中文。"
)

DEFAULT_MEDICAL_PROMPT = (
    "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防。"
)

DEFAULT_DEEPSEEK_API_KEY = "sk-3a9e371f8ab646c2ad5298f49b1fb063"
