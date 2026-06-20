from __future__ import annotations

import argparse
import json
import logging
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from hybrid_extractor.engine import HybridExtractionEngine
from hybrid_extractor.extractors.base import BaseFallbackExtractor
from hybrid_extractor.models import (
    ExtractionPlan,
    ExtractionRequest,
    ExtractionResult,
    FieldRule,
    FieldSelectorRule,
    TemplateManifest,
)
from hybrid_extractor.services.template_service import TemplateService


DEFAULT_MAPPING_PATH = Path(r"G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl")


class EmptyFallbackExtractor(BaseFallbackExtractor):
    def extract(self, request, intent) -> ExtractionResult:
        return ExtractionResult(data={})


def main() -> None:
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("HybridExtractionEngine").setLevel(logging.WARNING)
    logging.getLogger("hybrid_extractor").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Benchmark same-site template reuse on local HTML samples.")
    parser.add_argument("--mapping-path", type=Path, default=DEFAULT_MAPPING_PATH)
    parser.add_argument("--site", default="erj.ajcass.com")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if not args.mapping_path.exists():
        raise SystemExit(f"Mapping file not found: {args.mapping_path}")

    records = load_records(args.mapping_path, args.site, args.limit)
    if not records:
        raise SystemExit("No eligible records found.")

    with tempfile.TemporaryDirectory(prefix="template-benchmark-") as temp_dir:
        root = Path(temp_dir)
        service = TemplateService(
            template_dir=root / "templates",
            template_store_dir=root / "template_store",
            template_candidate_dir=root / "template_candidates",
        )
        seed_html = Path(records[0]["file_path"]).read_text(encoding="utf-8", errors="ignore")
        service.upsert_manifest(build_manifest_from_seed_html(seed_html, args.site))
        engine = HybridExtractionEngine(
            fallback_extractor=EmptyFallbackExtractor(),
            template_service=service,
        )

        results = []
        for record in records:
            html = Path(record["file_path"]).read_text(encoding="utf-8", errors="ignore")
            response = engine.extract(
                ExtractionRequest(
                    url=record["url"],
                    raw_html=html,
                    user_prompt="提取论文页面中的标题、作者、期刊、卷期、引用格式等结构化信息",
                )
            )
            match = response.debug_trace.get("template_match") or {}
            results.append(
                {
                    "url": record["url"],
                    "file_path": record["file_path"],
                    "status": response.status,
                    "extractor_type": response.extractor_type,
                    "template_id": response.template_id,
                    "coverage": response.validation_report.coverage,
                    "match_score": match.get("match_score"),
                    "selector_hit_rate": match.get("selector_hit_rate"),
                    "required_hit_rate": match.get("required_hit_rate"),
                }
            )

    deterministic_hits = [item for item in results if item["extractor_type"] == "deterministic"]
    summary = {
        "mapping_path": str(args.mapping_path),
        "site": args.site,
        "eligible_records": len(records),
        "deterministic_hits": len(deterministic_hits),
        "deterministic_hit_rate": round(len(deterministic_hits) / len(records), 4),
        "avg_coverage": round(sum(item["coverage"] for item in results) / len(results), 4),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def load_records(mapping_path: Path, site: str, limit: int) -> list[dict]:
    selected = []
    seen_paths = set()
    with mapping_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            url = record.get("url", "")
            file_path = record.get("file_path", "")
            if urlparse(url).netloc.lower() != site.lower():
                continue
            if not file_path or file_path in seen_paths:
                continue
            path = Path(file_path)
            if not path.exists():
                continue

            html = path.read_text(encoding="utf-8", errors="ignore")
            if not is_eligible_paper_html(html):
                continue

            selected.append(record)
            seen_paths.add(file_path)
            if len(selected) >= limit:
                break
    return selected


def is_eligible_paper_html(html: str) -> bool:
    return all(token in html for token in ['class="info-table"', "<h1>", "引用格式", "PDF"])


def build_manifest_from_seed_html(html: str, site: str) -> TemplateManifest:
    soup = BeautifulSoup(html, "html.parser")
    label_rules = []
    required_fields = ["title"]
    for index, row in enumerate(soup.select(".info-table tr"), start=1):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        label = cells[0].get_text(" ", strip=True)
        if not label:
            continue
        field_name = f"meta_{index}"
        label_rules.append(
            FieldRule(
                field_name=field_name,
                selectors=[FieldSelectorRule(kind="label_value", value=label)],
            )
        )
        if len(required_fields) < 4:
            required_fields.append(field_name)

    return TemplateManifest(
        template_id="ajcass_article_family_v1",
        parser_key="generic:rule",
        site_id=site,
        site_name=site,
        page_type="article_page",
        scenario="article_detail",
        version="v1",
        template_key="ajcass_article_family",
        lifecycle_status="active",
        active=True,
        required_fields=required_fields,
        extraction_plan=ExtractionPlan(
            fields=[
                FieldRule(field_name="title", selectors=[FieldSelectorRule(kind="css", value=".header h1")]),
                FieldRule(field_name="subtitle", selectors=[FieldSelectorRule(kind="css", value=".header .meta em")]),
                *label_rules,
            ]
        ),
        notes="Local benchmark manifest for AJCASS article detail pages.",
    )


if __name__ == "__main__":
    main()
