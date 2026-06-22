from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from bs4 import BeautifulSoup

from ..models import (
    ExtractionIntent,
    ExtractionRequest,
    ExtractionResult,
    PageClassification,
    TemplateMatch,
)
from ..rule_runtime import PageContext


class BaseTemplateParser(ABC):
    template_id: str
    parser_key: str
    site_id: str
    site_name: str
    page_type: str
    scenario: str

    @abstractmethod
    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
    ) -> Optional[TemplateMatch]:
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup | PageContext,
        intent: ExtractionIntent,
    ) -> ExtractionResult:
        raise NotImplementedError
