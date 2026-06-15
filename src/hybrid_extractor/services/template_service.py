from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ..config import TEMPLATE_CANDIDATE_DIR, TEMPLATE_DIR, TEMPLATE_STORE_DIR
from ..models import PageFingerprint, TemplateCandidate, TemplateManifest


class TemplateService:
    def __init__(
        self,
        template_dir: Path | None = None,
        template_store_dir: Path | None = None,
        template_candidate_dir: Path | None = None,
    ) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.template_store_dir = template_store_dir or TEMPLATE_STORE_DIR
        self.template_candidate_dir = template_candidate_dir or TEMPLATE_CANDIDATE_DIR
        self.template_store_dir.mkdir(parents=True, exist_ok=True)
        self.template_candidate_dir.mkdir(parents=True, exist_ok=True)

    def load_manifests(self) -> List[TemplateManifest]:
        manifests: list[TemplateManifest] = []
        for directory in (self.template_store_dir, self.template_dir):
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                if "parser_key" not in data:
                    continue
                manifests.append(TemplateManifest.model_validate(data))
        return manifests

    def get_manifest(self, template_id: str) -> Optional[TemplateManifest]:
        for manifest in self.load_manifests():
            if manifest.template_id == template_id:
                return manifest
        return None

    def upsert_manifest(self, manifest: TemplateManifest) -> Path:
        path = self.template_store_dir / f"{manifest.template_id}.json"
        path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def persist_candidate(self, candidate: TemplateCandidate) -> Path:
        path = self.template_candidate_dir / f"{candidate.candidate_id}.json"
        path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        return path

    def solidify_candidate(
        self,
        candidate: TemplateCandidate,
        required_fields: list[str],
    ) -> TemplateManifest | None:
        if candidate.proposed_plan is None or not candidate.proposed_plan.fields:
            return None
        plan_fields = {field.field_name for field in candidate.proposed_plan.fields}
        covered_required = [field for field in required_fields if field in plan_fields]
        if required_fields and len(covered_required) / len(required_fields) < 0.6:
            return None
        if "name" in required_fields and "name" not in plan_fields:
            return None

        existing = self.find_manifest_by_fingerprint(
            candidate.site_id,
            candidate.scenario,
            candidate.fingerprint,
        )
        if existing and existing.extraction_plan is not None:
            return existing

        template_id = self._build_template_id(candidate)
        manifest = TemplateManifest(
            template_id=template_id,
            parser_key="generic:rule",
            site_id=candidate.site_id,
            site_name=candidate.site_name,
            page_type=candidate.page_type,
            scenario=candidate.scenario,
            version="v1",
            fingerprint=candidate.fingerprint,
            required_fields=required_fields,
            extraction_plan=candidate.proposed_plan,
            notes="Auto-solidified from a successful LLM fallback candidate.",
        )
        self.upsert_manifest(manifest)
        return manifest

    def find_manifest_by_fingerprint(
        self,
        site_id: str,
        scenario: str,
        fingerprint: PageFingerprint,
    ) -> TemplateManifest | None:
        for manifest in self.load_manifests():
            if manifest.site_id != site_id or manifest.scenario != scenario:
                continue
            if manifest.fingerprint and manifest.fingerprint.dom_signature == fingerprint.dom_signature:
                return manifest
        return None

    def _build_template_id(self, candidate: TemplateCandidate) -> str:
        site = self._slug(candidate.site_id or "unknown")
        scenario = self._slug(candidate.scenario or "unknown")
        signature = candidate.fingerprint.dom_signature[:12]
        return f"{site}_{scenario}_{signature}_v1"

    def _slug(self, value: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "unknown"
