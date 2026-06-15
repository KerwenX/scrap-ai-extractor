from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATE_DIR = CONFIG_DIR / "templates"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_STORE_DIR = DATA_DIR / "template_store"
TEMPLATE_CANDIDATE_DIR = DATA_DIR / "template_candidates"
LOG_DIR = PROJECT_ROOT / "logs"

DEFAULT_OUTPUT_PROMPT = (
    "\u63d0\u53d6\u9875\u9762\u4e2d\u4e0e\u7528\u6237\u9700\u6c42\u6700\u76f8\u5173\u7684\u7ed3\u6784\u5316\u4fe1\u606f\uff0c\u5e76\u5c3d\u91cf\u8f93\u51fa\u4e2d\u6587\u3002"
)

DEFAULT_MEDICAL_PROMPT = (
    "\u63d0\u53d6\u75be\u75c5\u57fa\u672c\u4fe1\u606f\u3001\u75c5\u56e0\u3001\u75c7\u72b6\u3001\u8bca\u65ad\u3001\u6cbb\u7597\u3001\u65e5\u5e38\u6ce8\u610f\u4e8b\u9879\u548c\u9884\u9632\u3002"
)

DEFAULT_DEEPSEEK_API_KEY = "sk-3a9e371f8ab646c2ad5298f49b1fb063"
