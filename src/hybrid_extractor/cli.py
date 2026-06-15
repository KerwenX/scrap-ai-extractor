from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import DEFAULT_MEDICAL_PROMPT
from .controllers import ExtractionController


def read_html_file(file_path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return file_path.read_text(encoding="utf-8", errors="ignore")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="混合网页解析器")
    parser.add_argument("--html-path", required=True, help="本地 HTML 文件路径")
    parser.add_argument("--url", default="", help="原始页面 URL")
    parser.add_argument(
        "--prompt",
        default=DEFAULT_MEDICAL_PROMPT,
        help="自然语言抽取需求",
    )
    parser.add_argument("--output-file", default="", help="可选的输出 JSON 文件路径")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    html_path = Path(args.html_path)
    raw_html = read_html_file(html_path)
    controller = ExtractionController()
    payload = controller.extract(
        {
            "url": args.url,
            "raw_html": raw_html,
            "user_prompt": args.prompt,
        }
    )
    payload["source_file"] = str(html_path)

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    print(content)

    if args.output_file:
        Path(args.output_file).write_text(content, encoding="utf-8")
