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
    parser.add_argument("--html-path", help="单条解析时使用的本地 HTML 文件路径")
    parser.add_argument("--url", default="", help="原始页面 URL")
    parser.add_argument(
        "--prompt",
        default=DEFAULT_MEDICAL_PROMPT,
        help="自然语言抽取需求",
    )
    parser.add_argument("--output-file", default="", help="单条解析结果 JSON 输出路径")
    parser.add_argument("--template-only", action="store_true", help="单条解析仅允许命中正式模板")
    parser.add_argument("--batch-jsonl", default="", help="批量解析映射文件路径，JSONL 每行包含 url 和 html_path")
    parser.add_argument("--output-jsonl", default="", help="批量解析结果 JSONL 输出路径")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    controller = ExtractionController()

    if args.batch_jsonl:
        payload = controller.extract_batch(
            {
                "jsonl_path": args.batch_jsonl,
                "user_prompt": args.prompt,
                "output_jsonl_path": args.output_jsonl,
            }
        )
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        print(content)
        return

    if not args.html_path:
        raise SystemExit("Single extraction requires --html-path, or use --batch-jsonl for batch mode.")

    html_path = Path(args.html_path)
    raw_html = read_html_file(html_path)
    payload = controller.extract(
        {
            "url": args.url,
            "raw_html": raw_html,
            "user_prompt": args.prompt,
            "run_mode": "template_only" if args.template_only else "auto",
        }
    )
    payload["source_file"] = str(html_path)

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    print(content)

    if args.output_file:
        Path(args.output_file).write_text(content, encoding="utf-8")
