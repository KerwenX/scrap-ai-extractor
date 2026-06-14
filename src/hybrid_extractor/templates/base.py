from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from bs4 import BeautifulSoup

from ..models import ExtractionIntent, ExtractionRequest, ExtractionResult, TemplateMatch


class BaseTemplateParser(ABC):
    template_id: str
    site_name: str
    page_type: str

    @abstractmethod
    def match(
        self, request: ExtractionRequest, soup: BeautifulSoup, page_title: str
    ) -> Optional[TemplateMatch]:
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        intent: ExtractionIntent,
    ) -> ExtractionResult:
        raise NotImplementedError
