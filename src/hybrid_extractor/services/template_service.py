from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ..config import TEMPLATE_CANDIDATE_DIR, TEMPLATE_DIR, TEMPLATE_STORE_DIR
from ..models import TemplateCandidate, TemplateManifest


class TemplateService:
    def __init__(self) -> None:
        TEMPLATE_STORE_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATE_CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    def load_manifests(self) -> List[TemplateManifest]:
        manifests: list[TemplateManifest] = []
        for directory in (TEMPLATE_DIR, TEMPLATE_STORE_DIR):
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
        path = TEMPLATE_STORE_DIR / f"{manifest.template_id}.json"
        path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def persist_candidate(self, candidate: TemplateCandidate) -> Path:
        path = TEMPLATE_CANDIDATE_DIR / f"{candidate.candidate_id}.json"
        path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        return path
