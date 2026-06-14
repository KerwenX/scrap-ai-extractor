from __future__ import annotations

from typing import Optional, Tuple

from bs4 import BeautifulSoup

from .models import ExtractionRequest, PageClassification, TemplateMatch
from .templates import BaseTemplateParser, DayiDiseaseTemplateParser, DayiQATemplateParser


class TemplateRegistry:
    def __init__(self) -> None:
        self.parsers: list[BaseTemplateParser] = [
            DayiDiseaseTemplateParser(),
            DayiQATemplateParser(),
        ]

    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
    ) -> Tuple[Optional[TemplateMatch], Optional[BaseTemplateParser]]:
        best_match: Optional[TemplateMatch] = None
        best_parser: Optional[BaseTemplateParser] = None

        for parser in self.parsers:
            match = parser.match(request, soup, page_title, classification)
            if match is None:
                continue
            if best_match is None or match.match_score > best_match.match_score:
                best_match = match
                best_parser = parser

        return best_match, best_parser
