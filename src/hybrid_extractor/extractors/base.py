from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult


class BaseFallbackExtractor(ABC):
    @abstractmethod
    def extract(self, request: ExtractionRequest, intent: ExtractionIntent) -> ExtractionResult:
        raise NotImplementedError
