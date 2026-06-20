from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..engine import HybridExtractionEngine
from ..models import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    ExtractionRequest,
    ExtractionResponse,
)
from .template_service import TemplateService


class ExtractionService:
    def __init__(
        self,
        engine: HybridExtractionEngine | None = None,
        template_service: TemplateService | None = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.engine = engine or HybridExtractionEngine(template_service=self.template_service)

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        return self.engine.extract(request)

    def extract_batch(self, request: BatchExtractionRequest) -> BatchExtractionResponse:
        records = self._load_batch_records(request)
        output_path = self._resolve_output_path(request)
        results = []
        success_count = 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                html_path = Path(record["html_path"])
                if not html_path.exists():
                    result = {
                        "url": record["url"],
                        "html_path": str(html_path),
                        "status": "failed",
                        "error": f"HTML file not found: {html_path}",
                    }
                else:
                    raw_html = self._read_html_file(html_path)
                    response = self.engine.extract(
                        ExtractionRequest(
                            url=record["url"],
                            raw_html=raw_html,
                            user_prompt=request.user_prompt,
                            run_mode="template_only",
                        )
                    )
                    result = {
                        "url": record["url"],
                        "html_path": str(html_path),
                        **response.model_dump(),
                    }
                    if response.status == "success":
                        success_count += 1

                results.append(result)
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")

        return BatchExtractionResponse(
            request_id=request.request_id,
            status="success",
            output_jsonl_path=str(output_path),
            total_count=len(results),
            success_count=success_count,
            failed_count=len(results) - success_count,
            results=results,
        )

    def _load_batch_records(self, request: BatchExtractionRequest) -> list[dict[str, str]]:
        jsonl_content = request.jsonl_content.strip()
        if not jsonl_content:
            if not request.jsonl_path.strip():
                raise ValueError("Batch extraction requires jsonl_path or jsonl_content.")
            jsonl_path = Path(request.jsonl_path)
            if not jsonl_path.exists():
                raise ValueError(f"Batch mapping file not found: {jsonl_path}")
            jsonl_content = jsonl_path.read_text(encoding="utf-8", errors="ignore")

        records: list[dict[str, str]] = []
        for line_number, raw_line in enumerate(jsonl_content.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc

            url = str(payload.get("url", "")).strip()
            html_path = str(payload.get("html_path") or payload.get("file_path") or "").strip()
            if not url:
                raise ValueError(f"Batch record line {line_number} is missing url.")
            if not html_path:
                raise ValueError(f"Batch record line {line_number} is missing html_path.")
            records.append({"url": url, "html_path": html_path})

        if not records:
            raise ValueError("Batch mapping file contains no valid records.")
        return records

    def _resolve_output_path(self, request: BatchExtractionRequest) -> Path:
        if request.output_jsonl_path.strip():
            return Path(request.output_jsonl_path)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return Path("data") / "batch_results" / f"batch-extraction-{timestamp}.jsonl"

    def _read_html_file(self, file_path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return file_path.read_text(encoding="utf-8", errors="ignore")
