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
