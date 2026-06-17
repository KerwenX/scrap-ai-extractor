from __future__ import annotations

import json
import re
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
                manifests.append(self._normalize_manifest(TemplateManifest.model_validate(data)))
        return manifests

    def load_candidates(self) -> List[TemplateCandidate]:
        candidates: list[TemplateCandidate] = []
        if not self.template_candidate_dir.exists():
            return candidates
        for path in sorted(self.template_candidate_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            candidates.append(TemplateCandidate.model_validate(data))
        return candidates

    def get_manifest(self, template_id: str) -> Optional[TemplateManifest]:
        for manifest in self.load_manifests():
            if manifest.template_id == template_id:
                return manifest
        return None

    def get_candidate(self, candidate_id: str) -> Optional[TemplateCandidate]:
        path = self.template_candidate_dir / f"{candidate_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return TemplateCandidate.model_validate(data)

    def delete_manifest(self, template_id: str) -> bool:
        path = self.template_store_dir / f"{template_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_manifests(self, template_ids: list[str]) -> int:
        deleted = 0
        for template_id in template_ids:
            if self.delete_manifest(template_id):
                deleted += 1
        return deleted

    def delete_candidate(self, candidate_id: str) -> bool:
        path = self.template_candidate_dir / f"{candidate_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def upsert_manifest(self, manifest: TemplateManifest) -> Path:
        manifest = self._normalize_manifest(manifest)
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

    def set_manifest_active(self, template_id: str, active: bool) -> Optional[TemplateManifest]:
        manifest = self.get_manifest(template_id)
        if manifest is None:
            return None
        updated = self._normalize_manifest(
            manifest.model_copy(
                update={
                    "active": active,
                    "lifecycle_status": "active" if active else "deprecated",
                }
            )
        )
        self.upsert_manifest(updated)
        return updated

    def set_manifest_status(
        self,
        template_id: str,
        lifecycle_status: str,
    ) -> Optional[TemplateManifest]:
        manifest = self.get_manifest(template_id)
        if manifest is None:
            return None
        updated = self._normalize_manifest(
            manifest.model_copy(update={"lifecycle_status": lifecycle_status})
        )
        self.upsert_manifest(updated)
        return updated

    def promote_candidate(
        self,
        candidate_id: str,
        template_key: str | None = None,
        required_fields: list[str] | None = None,
        deactivate_previous_versions: bool = False,
    ) -> TemplateManifest | None:
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            return None
        return self.promote_candidate_instance(
            candidate,
            template_key=template_key,
            required_fields=required_fields,
            deactivate_previous_versions=deactivate_previous_versions,
        )

    def promote_candidate_instance(
        self,
        candidate: TemplateCandidate,
        template_key: str | None = None,
        required_fields: list[str] | None = None,
        deactivate_previous_versions: bool = False,
    ) -> TemplateManifest | None:
        if candidate.proposed_plan is None or not candidate.proposed_plan.fields:
            return None

        existing = self.find_manifest_by_fingerprint(
            candidate.site_id,
            candidate.scenario,
            candidate.fingerprint,
        )
        if existing and existing.extraction_plan is not None:
            return existing

        normalized_key = self._normalize_template_key(template_key or self._default_template_key(candidate))
        version = self._next_version_for_key(normalized_key)
        template_id = f"{normalized_key}_{version}"
        manifest = TemplateManifest(
            template_id=template_id,
            parser_key="generic:rule",
            site_id=candidate.site_id,
            site_name=candidate.site_name,
            page_type=candidate.page_type,
            scenario=candidate.scenario,
            version=version,
            template_key=normalized_key,
            lifecycle_status="active",
            active=True,
            fingerprint=candidate.fingerprint,
            required_fields=required_fields or candidate.extracted_fields,
            extraction_plan=candidate.proposed_plan,
            notes="Promoted from template candidate.",
            source_candidate_id=candidate.candidate_id,
        )

        if deactivate_previous_versions:
            self._deactivate_manifests_by_key(normalized_key)

        self.upsert_manifest(manifest)
        return manifest

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

        manifest = self.promote_candidate_instance(
            candidate,
            template_key=self._build_template_key_from_signature(candidate),
            required_fields=required_fields,
            deactivate_previous_versions=False,
        )
        if manifest is None:
            return None
        manifest = manifest.model_copy(
            update={"notes": "Auto-solidified from a successful LLM fallback candidate."}
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
        template_key = self._build_template_key_from_signature(candidate)
        return f"{template_key}_v1"

    def _build_template_key_from_signature(self, candidate: TemplateCandidate) -> str:
        site = self._slug(candidate.site_id or "unknown")
        scenario = self._slug(candidate.scenario or "unknown")
        signature = candidate.fingerprint.dom_signature[:12]
        return f"{site}_{scenario}_{signature}"

    def _default_template_key(self, candidate: TemplateCandidate) -> str:
        site = self._slug(candidate.site_id or "unknown")
        scenario = self._slug(candidate.scenario or "unknown")
        return f"{site}_{scenario}"

    def _normalize_template_key(self, value: str) -> str:
        normalized = self._slug(value)
        return re.sub(r"_v\d+$", "", normalized)

    def _next_version_for_key(self, template_key: str) -> str:
        max_version = 0
        for manifest in self.load_manifests():
            manifest_key = self._manifest_template_key(manifest)
            if manifest_key != template_key:
                continue
            match = re.search(r"v(\d+)$", manifest.version or "")
            if match:
                max_version = max(max_version, int(match.group(1)))
        return f"v{max_version + 1}"

    def _manifest_template_key(self, manifest: TemplateManifest) -> str:
        if manifest.template_key:
            return manifest.template_key
        return re.sub(r"_v\d+$", "", manifest.template_id)

    def _deactivate_manifests_by_key(self, template_key: str) -> None:
        for manifest in self.load_manifests():
            if self._manifest_template_key(manifest) != template_key:
                continue
            if not manifest.active and manifest.lifecycle_status != "active":
                continue
            self.upsert_manifest(
                self._normalize_manifest(
                    manifest.model_copy(update={"active": False, "lifecycle_status": "deprecated"})
                )
            )

    def _normalize_manifest(self, manifest: TemplateManifest) -> TemplateManifest:
        lifecycle_status = manifest.lifecycle_status or ("active" if manifest.active else "deprecated")
        if lifecycle_status == "active":
            active = True
        elif lifecycle_status in {"deprecated", "archived"}:
            active = False
        else:
            active = manifest.active
        return manifest.model_copy(update={"lifecycle_status": lifecycle_status, "active": active})

    def _slug(self, value: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "unknown"
