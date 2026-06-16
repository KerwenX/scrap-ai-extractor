from __future__ import annotations

from typing import Any, Dict

from ..models import ExtractionRequest
from ..services.extraction_service import ExtractionService
from ..services.template_service import TemplateService


class ExtractionController:
    def __init__(
        self,
        extraction_service: ExtractionService | None = None,
        template_service: TemplateService | None = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.extraction_service = extraction_service or ExtractionService(
            template_service=self.template_service
        )

    def extract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = ExtractionRequest.model_validate(payload)
        response = self.extraction_service.extract(request)
        return response.model_dump()

    def list_templates(self) -> Dict[str, Any]:
        manifests = [manifest.model_dump() for manifest in self.template_service.load_manifests()]
        return {"templates": manifests}

    def get_template(self, template_id: str) -> Dict[str, Any]:
        manifest = self.template_service.get_manifest(template_id)
        if manifest is None:
            raise ValueError(f"Template not found: {template_id}")
        return manifest.model_dump()

    def list_template_candidates(self) -> Dict[str, Any]:
        candidates = [candidate.model_dump() for candidate in self.template_service.load_candidates()]
        return {"candidates": candidates}

    def get_template_candidate(self, candidate_id: str) -> Dict[str, Any]:
        candidate = self.template_service.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"Template candidate not found: {candidate_id}")
        return candidate.model_dump()

    def set_template_active(self, template_id: str, active: bool) -> Dict[str, Any]:
        manifest = self.template_service.set_manifest_active(template_id, active)
        if manifest is None:
            raise ValueError(f"Template not found: {template_id}")
        return manifest.model_dump()
