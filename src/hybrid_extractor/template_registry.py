from __future__ import annotations

from typing import Optional, Tuple

from bs4 import BeautifulSoup

from .fingerprinting import compare_fingerprints
from .models import ExtractionRequest, PageClassification, TemplateMatch
from .services.template_service import TemplateService
from .templates import (
    BaseTemplateParser,
    DayiDiseaseTemplateParser,
    DayiQATemplateParser,
    GenericRuleTemplateParser,
)


class TemplateRegistry:
    def __init__(self, template_service: TemplateService | None = None) -> None:
        self.template_service = template_service or TemplateService()
        self.parsers: list[BaseTemplateParser] = [
            DayiDiseaseTemplateParser(),
            DayiQATemplateParser(),
        ]
        self.parsers_by_key = {parser.parser_key: parser for parser in self.parsers}

    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
        fingerprint=None,
    ) -> Tuple[Optional[TemplateMatch], Optional[BaseTemplateParser]]:
        if fingerprint is not None:
            for manifest in self.template_service.load_manifests():
                if manifest.site_id != classification.site_id or manifest.scenario != classification.scenario:
                    continue
                if not manifest.fingerprint:
                    continue
                similarity = compare_fingerprints(fingerprint, manifest.fingerprint)
                if similarity < 0.8:
                    continue
                parser = self.parsers_by_key.get(manifest.parser_key)
                if parser is None and manifest.extraction_plan is not None:
                    parser = GenericRuleTemplateParser(manifest)
                if parser is None:
                    continue
                return (
                    TemplateMatch(
                        template_id=manifest.template_id,
                        site_id=manifest.site_id,
                        site_name=manifest.site_name,
                        match_score=similarity,
                        page_type=manifest.page_type,
                        scenario=manifest.scenario,
                        version=manifest.version,
                    ),
                    parser,
                )

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
