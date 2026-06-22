from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Iterator

from ..engine import HybridExtractionEngine
from ..models import BatchExtractionRequest, BatchExtractionResponse, ExtractionRequest, ExtractionResponse
from .template_service import TemplateService

_BATCH_ENGINE: HybridExtractionEngine | None = None


def _init_batch_worker(
    template_dir: str,
    template_store_dir: str,
    template_candidate_dir: str,
    include_builtin_templates: bool,
) -> None:
    global _BATCH_ENGINE
    service = TemplateService(
        template_dir=Path(template_dir),
        template_store_dir=Path(template_store_dir),
        template_candidate_dir=Path(template_candidate_dir),
        include_builtin_templates=include_builtin_templates,
        frozen_manifests=True,
    )
    _BATCH_ENGINE = HybridExtractionEngine(template_service=service)


def _process_batch_record(payload: dict[str, str]) -> dict:
    global _BATCH_ENGINE
    if _BATCH_ENGINE is None:
        raise RuntimeError("Batch worker engine is not initialized.")

    html_path = Path(payload["html_path"])
    if not html_path.exists():
        return {
            "url": payload["url"],
            "html_path": str(html_path),
            "status": "failed",
            "error": f"HTML file not found: {html_path}",
        }

    raw_html = _read_html_file(html_path)
    response = _BATCH_ENGINE.extract(
        ExtractionRequest(
            url=payload["url"],
            raw_html=raw_html,
            user_prompt=payload["user_prompt"],
            run_mode="template_only",
        )
    )
    return {
        "url": payload["url"],
        "html_path": str(html_path),
        **response.model_dump(),
    }


def _read_html_file(file_path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return file_path.read_text(encoding="utf-8", errors="ignore")


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
        output_path = self._resolve_output_path(request)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total_count = 0
        success_count = 0
        failed_count = 0
        sample_errors: list[dict] = []
        sample_successes: list[dict] = []

        iterator = self._iter_batch_records(request)
        result_iter = self._batch_result_iterator(request, iterator)

        with output_path.open("w", encoding="utf-8") as handle:
            for result in result_iter:
                total_count += 1
                if result.get("status") == "success":
                    success_count += 1
                    if len(sample_successes) < request.sample_limit:
                        sample_successes.append(result)
                else:
                    failed_count += 1
                    if len(sample_errors) < request.sample_limit:
                        sample_errors.append(result)
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")

        return BatchExtractionResponse(
            request_id=request.request_id,
            status="success",
            output_jsonl_path=str(output_path),
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            results=[],
            sample_errors=sample_errors,
            sample_successes=sample_successes,
        )

    def _batch_result_iterator(
        self,
        request: BatchExtractionRequest,
        records: Iterator[dict[str, str]],
    ) -> Iterator[dict]:
        max_workers = max(1, int(request.max_workers or 1))
        if max_workers == 1:
            for record in records:
                yield self._process_record_inline(record, request.user_prompt)
            return

        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_batch_worker,
            initargs=(
                str(self.template_service.template_dir),
                str(self.template_service.template_store_dir),
                str(self.template_service.template_candidate_dir),
                bool(self.template_service.include_builtin_templates),
            ),
        ) as executor:
            payloads = (
                {
                    "url": record["url"],
                    "html_path": record["html_path"],
                    "user_prompt": request.user_prompt,
                }
                for record in records
            )
            for result in executor.map(_process_batch_record, payloads, chunksize=16):
                yield result

    def _process_record_inline(self, record: dict[str, str], user_prompt: str) -> dict:
        html_path = Path(record["html_path"])
        if not html_path.exists():
            return {
                "url": record["url"],
                "html_path": str(html_path),
                "status": "failed",
                "error": f"HTML file not found: {html_path}",
            }

        raw_html = _read_html_file(html_path)
        response = self.engine.extract(
            ExtractionRequest(
                url=record["url"],
                raw_html=raw_html,
                user_prompt=user_prompt,
                run_mode="template_only",
            )
        )
        return {
            "url": record["url"],
            "html_path": str(html_path),
            **response.model_dump(),
        }

    def _iter_batch_records(self, request: BatchExtractionRequest) -> Iterator[dict[str, str]]:
        jsonl_content = request.jsonl_content.strip()
        if jsonl_content:
            for line_number, raw_line in enumerate(jsonl_content.splitlines(), start=1):
                record = self._parse_batch_line(raw_line, line_number)
                if record is not None:
                    yield record
            return

        if not request.jsonl_path.strip():
            raise ValueError("Batch extraction requires jsonl_path or jsonl_content.")
        jsonl_path = Path(request.jsonl_path)
        if not jsonl_path.exists():
            raise ValueError(f"Batch mapping file not found: {jsonl_path}")

        seen_any = False
        with jsonl_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                record = self._parse_batch_line(raw_line, line_number)
                if record is None:
                    continue
                seen_any = True
                yield record
        if not seen_any:
            raise ValueError("Batch mapping file contains no valid records.")

    def _parse_batch_line(self, raw_line: str, line_number: int) -> dict[str, str] | None:
        line = raw_line.strip()
        if not line:
            return None
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
        return {"url": url, "html_path": html_path}

    def _resolve_output_path(self, request: BatchExtractionRequest) -> Path:
        if request.output_jsonl_path.strip():
            return Path(request.output_jsonl_path)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return Path("data") / "batch_results" / f"batch-extraction-{timestamp}.jsonl"
