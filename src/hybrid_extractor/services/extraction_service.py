from __future__ import annotations

from ..engine import HybridExtractionEngine
from ..models import ExtractionRequest, ExtractionResponse
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
