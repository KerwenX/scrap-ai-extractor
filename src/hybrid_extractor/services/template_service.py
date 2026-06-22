from __future__ import annotations

import json
import re
from hashlib import sha1
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qsl, urlparse

from ..config import TEMPLATE_CANDIDATE_DIR, TEMPLATE_DIR, TEMPLATE_STORE_DIR, load_app_settings
from ..models import ExtractionPlan, PageFingerprint, TemplateCandidate, TemplateManifest


class TemplateService:
    def __init__(
        self,
        template_dir: Path | None = None,
        template_store_dir: Path | None = None,
        template_candidate_dir: Path | None = None,
        include_builtin_templates: bool | None = None,
        frozen_manifests: bool = False,
    ) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.template_store_dir = template_store_dir or TEMPLATE_STORE_DIR
        self.template_candidate_dir = template_candidate_dir or TEMPLATE_CANDIDATE_DIR
        if include_builtin_templates is None:
            include_builtin_templates = load_app_settings().builtin_templates_enabled
        self.include_builtin_templates = include_builtin_templates
        self.frozen_manifests = frozen_manifests
        self.template_store_dir.mkdir(parents=True, exist_ok=True)
        self.template_candidate_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_cache: list[TemplateManifest] | None = None
        self._manifest_cache_signature: tuple | None = None
        self._manifest_cache_by_id: dict[str, TemplateManifest] = {}
        self._candidate_cache: list[TemplateCandidate] | None = None
        self._candidate_cache_signature: tuple | None = None

    def load_manifests(self) -> List[TemplateManifest]:
        directories = (
            (self.template_store_dir, self.template_dir)
            if self.include_builtin_templates
            else (self.template_store_dir,)
        )
        signature = None if self.frozen_manifests else self._directory_signature(directories)
        if self.frozen_manifests and self._manifest_cache is not None:
            return list(self._manifest_cache)
        if self._manifest_cache is not None and signature == self._manifest_cache_signature:
            return list(self._manifest_cache)

        manifests: list[TemplateManifest] = []
        for directory in directories:
            if not directory.exists():
                continue
            for path in self._iter_json_files(directory):
                data = json.loads(path.read_text(encoding="utf-8"))
                if "parser_key" not in data:
                    continue
                manifests.append(self._normalize_manifest(TemplateManifest.model_validate(data)))
        self._manifest_cache = manifests
        self._manifest_cache_signature = signature
        self._manifest_cache_by_id = {manifest.template_id: manifest for manifest in manifests}
        return manifests

    def load_candidates(self) -> List[TemplateCandidate]:
        signature = self._directory_signature((self.template_candidate_dir,))
        if self._candidate_cache is not None and signature == self._candidate_cache_signature:
            return list(self._candidate_cache)

        candidates: list[TemplateCandidate] = []
        if not self.template_candidate_dir.exists():
            return candidates
        for path in sorted(self.template_candidate_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            candidates.append(TemplateCandidate.model_validate(data))
        self._candidate_cache = candidates
        self._candidate_cache_signature = signature
        return candidates

    def get_manifest(self, template_id: str) -> Optional[TemplateManifest]:
        self.load_manifests()
        return self._manifest_cache_by_id.get(template_id)

    def get_candidate(self, candidate_id: str) -> Optional[TemplateCandidate]:
        path = self.template_candidate_dir / f"{candidate_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return TemplateCandidate.model_validate(data)

    def inspect_candidate_promotability(
        self,
        candidate: TemplateCandidate,
        required_fields: list[str] | None = None,
    ) -> dict:
        reasons: list[str] = []
        if candidate.proposed_plan is None:
            reasons.append("候选模板缺少 proposed_plan，当前没有可执行的 DSL 抽取方案。")
        elif not candidate.proposed_plan.fields:
            reasons.append("候选模板的 proposed_plan 为空，当前没有可执行字段规则。")

        if (
            candidate.proposed_plan is None
            and isinstance(candidate.sample_data, dict)
            and len(candidate.sample_data) == 1
            and isinstance(candidate.sample_data.get("content"), dict)
        ):
            reasons.append(
                "当前候选模板只抽取到了 content 对象，尚未拆解成可复用字段，因此不能直接晋升。"
            )

        if not candidate.extracted_fields:
            reasons.append("候选模板没有 extracted_fields，缺少字段沉淀信息。")

        if candidate.fingerprint is None or not candidate.fingerprint.dom_signature:
            reasons.append("候选模板缺少页面指纹，无法安全匹配正式模板。")

        existing = self._resolve_upgrade_target(candidate)

        if required_fields and candidate.proposed_plan is not None and candidate.proposed_plan.fields:
            plan_fields = {field.field_name for field in candidate.proposed_plan.fields}
            missing_required = [field for field in required_fields if field not in plan_fields]
            if missing_required:
                reasons.append("候选模板缺少部分必填字段规则：" + ", ".join(missing_required))

        existing_plan_fields = self._plan_field_names(existing.extraction_plan) if existing else set()
        candidate_plan_fields = self._plan_field_names(candidate.proposed_plan)
        target_fields = self._target_fields(candidate, required_fields)

        action = "blocked"
        action_label = "不可晋升"
        detail = ""
        if not reasons:
            if existing is None:
                action = "create"
                action_label = "新建正式模板"
                detail = "当前不存在同指纹正式模板，可以直接固化为新模板。"
            else:
                comparison = self._compare_candidate_to_existing(
                    candidate_plan_fields,
                    existing_plan_fields,
                    target_fields,
                )
                if comparison["should_upgrade"]:
                    action = "upgrade"
                    action_label = "升级既有模板"
                    detail = f"候选规则覆盖更完整，建议基于 {existing.template_id} 生成新版本。"
                else:
                    action = "reuse"
                    action_label = "已被既有模板覆盖"
                    detail = (
                        f"既有正式模板 {existing.template_id} 已覆盖当前候选规则，无需再次晋升。"
                    )

        return {
            "promotable": action in {"create", "upgrade"},
            "action": action,
            "action_label": action_label,
            "detail": detail,
            "reasons": reasons,
            "existing_template_id": existing.template_id if existing else None,
            "has_plan": bool(candidate.proposed_plan and candidate.proposed_plan.fields),
            "extracted_field_count": len(candidate.extracted_fields),
            "candidate_field_count": len(candidate_plan_fields),
            "existing_field_count": len(existing_plan_fields),
        }

    def delete_manifest(self, template_id: str) -> bool:
        path = self._find_manifest_path(template_id)
        if path is not None and path.exists():
            path.unlink()
            self._cleanup_empty_parent_dirs(path.parent, self.template_store_dir)
            self._invalidate_manifest_cache()
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
            self._invalidate_candidate_cache()
            return True
        return False

    def upsert_manifest(self, manifest: TemplateManifest) -> Path:
        manifest = self._normalize_manifest(manifest)
        path = self._manifest_storage_path(manifest)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        self._invalidate_manifest_cache()
        return path

    def persist_candidate(self, candidate: TemplateCandidate) -> Path:
        path = self.template_candidate_dir / f"{candidate.candidate_id}.json"
        path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        self._invalidate_candidate_cache()
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

        existing = self._resolve_upgrade_target(candidate)
        if existing is not None:
            check = self.inspect_candidate_promotability(candidate, required_fields)
            if check["action"] == "reuse":
                return existing
            if check["action"] == "blocked":
                return None
            if check["action"] == "upgrade":
                normalized_key = self._normalize_template_key(
                    template_key or existing.template_key or self._default_template_key(candidate)
                )
                version = self._next_version_for_key(normalized_key)
                template_id = f"{normalized_key}_{version}"
                self._deactivate_manifests_by_key(normalized_key)
                manifest = TemplateManifest(
                    template_id=template_id,
                    parser_key="generic:rule",
                    site_id=candidate.site_id,
                    site_name=candidate.site_name,
                    page_type=candidate.page_type,
                    scenario=candidate.scenario,
                    version=version,
                    template_key=normalized_key,
                    url_pattern=self._normalize_url_pattern(candidate.source_url),
                    url_pattern_hash=self._build_url_pattern_hash(candidate.source_url),
                    lifecycle_status="active",
                    active=True,
                    fingerprint=candidate.fingerprint,
                    required_fields=required_fields or candidate.extracted_fields,
                    extraction_plan=candidate.proposed_plan,
                    notes=f"Upgraded from template {existing.template_id} using candidate {candidate.candidate_id}.",
                    source_candidate_id=candidate.candidate_id,
                )
                self.upsert_manifest(manifest)
                return manifest

        normalized_key = self._normalize_template_key(
            template_key or self._build_template_key_from_signature(candidate)
        )
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
            url_pattern=self._normalize_url_pattern(candidate.source_url),
            url_pattern_hash=self._build_url_pattern_hash(candidate.source_url),
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
        structural_required = self._structural_required_fields(candidate.proposed_plan)
        covered_required = [field for field in required_fields if field in plan_fields]
        if not structural_required:
            if required_fields and len(covered_required) / len(required_fields) < 0.6:
                return None
            if "name" in required_fields and "name" not in plan_fields:
                return None

        effective_required_fields = structural_required or covered_required or sorted(plan_fields)
        manifest = self.promote_candidate_instance(
            candidate,
            template_key=None,
            required_fields=effective_required_fields,
            deactivate_previous_versions=False,
        )
        if manifest is None:
            return None
        manifest = manifest.model_copy(
            update={"notes": "Auto-solidified from a successful LLM fallback candidate."}
        )
        self.upsert_manifest(manifest)
        return manifest

    def _resolve_upgrade_target(self, candidate: TemplateCandidate) -> TemplateManifest | None:
        if not candidate.matched_template_id:
            return None
        return self.get_manifest(candidate.matched_template_id)

    def find_manifest_by_fingerprint(
        self,
        site_id: str,
        scenario: str,
        fingerprint: PageFingerprint,
    ) -> TemplateManifest | None:
        for manifest in self.load_manifests():
            if not self._site_matches(manifest.site_id, site_id) or manifest.scenario != scenario:
                continue
            if manifest.fingerprint and manifest.fingerprint.dom_signature == fingerprint.dom_signature:
                return manifest
        return None

    def _build_template_id(self, candidate: TemplateCandidate) -> str:
        template_key = self._build_template_key_from_signature(candidate)
        return f"{template_key}_v1"

    def _build_template_key_from_signature(self, candidate: TemplateCandidate) -> str:
        site = self._slug(self._site_family(candidate.site_id) or candidate.site_id or "unknown")
        scenario = self._slug(candidate.scenario or "unknown")
        page_type = self._slug(candidate.page_type or "unknown")
        url_hash = self._build_url_pattern_hash(candidate.source_url)
        signature = candidate.fingerprint.dom_signature[:12]
        return f"{site}_{scenario}_{page_type}_{url_hash}_{signature}"

    def _default_template_key(self, candidate: TemplateCandidate) -> str:
        site = self._slug(self._site_family(candidate.site_id) or candidate.site_id or "unknown")
        scenario = self._slug(candidate.scenario or "unknown")
        page_type = self._slug(candidate.page_type or "unknown")
        url_hash = self._build_url_pattern_hash(candidate.source_url)
        return f"{site}_{scenario}_{page_type}_{url_hash}"

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
            return self._canonical_template_key(manifest.template_key)
        return re.sub(r"_v\d+$", "", manifest.template_id)

    def _canonical_template_key(self, template_key: str) -> str:
        normalized = re.sub(r"_v\d+$", "", template_key)
        return re.sub(r"_[0-9a-f]{12}$", "", normalized)

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
        updates = {"lifecycle_status": lifecycle_status, "active": active}
        if not manifest.url_pattern_hash and manifest.source_candidate_id is None:
            updates["url_pattern_hash"] = self._infer_url_pattern_hash_from_template_key(manifest.template_key)
        elif not manifest.url_pattern_hash:
            updates["url_pattern_hash"] = self._infer_url_pattern_hash_from_template_key(manifest.template_key)
        if not manifest.url_pattern:
            updates["url_pattern"] = self._infer_url_pattern_from_template_key(manifest.template_key)

        if manifest.extraction_plan and manifest.extraction_plan.fields:
            plan_fields = [field.field_name for field in manifest.extraction_plan.fields]
            current_required = list(manifest.required_fields)
            overlap = [field for field in current_required if field in plan_fields]

            if not current_required:
                updates["required_fields"] = plan_fields
            elif len(overlap) / len(current_required) < 0.6:
                updates["required_fields"] = overlap if overlap else plan_fields

        return manifest.model_copy(update=updates)

    def _plan_field_names(self, plan: ExtractionPlan | None) -> set[str]:
        if plan is None or not plan.fields:
            return set()
        return {field.field_name for field in plan.fields}

    def _target_fields(
        self,
        candidate: TemplateCandidate,
        required_fields: list[str] | None,
    ) -> list[str]:
        if required_fields:
            return list(required_fields)
        if candidate.extracted_fields:
            return list(candidate.extracted_fields)
        return sorted(self._plan_field_names(candidate.proposed_plan))

    def _structural_required_fields(self, plan: ExtractionPlan | None) -> list[str]:
        if plan is None or not plan.fields:
            return []

        required: list[str] = []
        for field in plan.fields:
            kinds = {selector.kind for selector in field.selectors}
            if field.field_name == "标题" and field.field_name not in required:
                required.append(field.field_name)
                continue
            if {"all_label_values", "all_sections"} & kinds and field.field_name not in required:
                required.append(field.field_name)
        return required

    def _compare_candidate_to_existing(
        self,
        candidate_fields: set[str],
        existing_fields: set[str],
        target_fields: list[str],
    ) -> dict[str, float | bool]:
        if not existing_fields:
            coverage = 1.0 if candidate_fields else 0.0
            return {
                "candidate_coverage": coverage,
                "existing_coverage": 0.0,
                "coverage_delta": coverage,
                "should_upgrade": bool(candidate_fields),
            }

        target_set = set(target_fields or sorted(candidate_fields | existing_fields))
        candidate_coverage = len(candidate_fields & target_set) / len(target_set) if target_set else 0.0
        existing_coverage = len(existing_fields & target_set) / len(target_set) if target_set else 0.0
        coverage_delta = candidate_coverage - existing_coverage
        richer_fields = len(candidate_fields) > len(existing_fields)
        should_upgrade = coverage_delta >= 0.15 or (
            candidate_coverage >= existing_coverage and richer_fields
        )
        return {
            "candidate_coverage": round(candidate_coverage, 4),
            "existing_coverage": round(existing_coverage, 4),
            "coverage_delta": round(coverage_delta, 4),
            "should_upgrade": should_upgrade,
        }

    def _slug(self, value: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "unknown"

    def _build_url_pattern_hash(self, url: str) -> str:
        normalized = self._normalize_url_pattern(url)
        return sha1(normalized.encode("utf-8")).hexdigest()[:8]

    def build_url_pattern_hash_for_url(self, url: str) -> str:
        return self._build_url_pattern_hash(url)

    def _normalize_url_pattern(self, url: str) -> str:
        if not url:
            return "no_url"
        parsed = urlparse(url)
        raw_host = (parsed.netloc or parsed.path or "unknown").lower()
        host = self._site_family(raw_host) or raw_host
        path = parsed.path or "/"
        normalized_segments: list[str] = []
        for segment in path.split("/"):
            if not segment:
                continue
            if segment.isdigit():
                normalized_segments.append("{int}")
                continue
            if re.fullmatch(r"[0-9a-fA-F]{8,}", segment):
                normalized_segments.append("{hex}")
                continue
            replaced = re.sub(r"\d+", "{n}", segment.lower())
            normalized_segments.append(replaced)
        normalized_path = "/" + "/".join(normalized_segments)
        query_keys = sorted(key for key, _ in parse_qsl(parsed.query, keep_blank_values=True))
        query_part = "&".join(query_keys)
        return f"{host}|{normalized_path}|{query_part}"

    def _infer_url_pattern_hash_from_template_key(self, template_key: str) -> str:
        if not template_key:
            return ""
        normalized = re.sub(r"_v\d+$", "", template_key)
        match = re.search(r"_([0-9a-f]{8})(?:_[0-9a-f]{12})?$", normalized)
        if not match:
            return ""
        return match.group(1)

    def _infer_url_pattern_from_template_key(self, template_key: str) -> str:
        return ""

    def _site_matches(self, left: str, right: str) -> bool:
        return bool(left and right and self._site_family(left) == self._site_family(right))

    def _site_family(self, site_id: str) -> str:
        site_id = (site_id or "").strip().lower()
        if not site_id or site_id == "unknown":
            return ""

        host = urlparse(f"https://{site_id}").netloc or site_id
        if host.startswith("www."):
            host = host[4:]

        parts = [part for part in host.split(".") if part]
        if len(parts) <= 2:
            return host
        if len(parts[-1]) == 2 and len(parts[-2]) <= 3:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])

    def _directory_signature(self, directories: tuple[Path, ...]) -> tuple:
        signature: list[tuple[str, int, int]] = []
        for directory in directories:
            if not directory.exists():
                continue
            for path in self._iter_json_files(directory):
                stat = path.stat()
                signature.append((str(path), stat.st_mtime_ns, stat.st_size))
        return tuple(signature)

    def _manifest_storage_path(self, manifest: TemplateManifest) -> Path:
        site_folder = self._storage_site_folder(manifest.site_id)
        return self.template_store_dir / site_folder / f"{manifest.template_id}.json"

    def _find_manifest_path(self, template_id: str) -> Path | None:
        direct = self.template_store_dir / f"{template_id}.json"
        if direct.exists():
            return direct
        for path in self._iter_json_files(self.template_store_dir):
            if path.name == f"{template_id}.json":
                return path
        return None

    def _iter_json_files(self, directory: Path) -> list[Path]:
        return sorted(
            (path for path in directory.rglob("*.json") if path.is_file()),
            key=lambda path: str(path.relative_to(directory)).lower(),
        )

    def _storage_site_folder(self, site_id: str | None) -> str:
        raw = (site_id or "").strip().lower()
        if not raw:
            return "unknown"
        host = urlparse(f"https://{raw}").netloc or raw
        host = host.replace(":", "_")
        return self._slug(host)

    def _cleanup_empty_parent_dirs(self, start_dir: Path, stop_dir: Path) -> None:
        current = start_dir
        stop_dir = stop_dir.resolve()
        while current.exists():
            try:
                if current.resolve() == stop_dir:
                    break
            except FileNotFoundError:
                break
            if any(current.iterdir()):
                break
            current.rmdir()
            current = current.parent

    def _invalidate_manifest_cache(self) -> None:
        self._manifest_cache = None
        self._manifest_cache_signature = None
        self._manifest_cache_by_id = {}

    def _invalidate_candidate_cache(self) -> None:
        self._candidate_cache = None
        self._candidate_cache_signature = None
