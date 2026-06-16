from __future__ import annotations

from typing import Optional, Tuple

from bs4 import BeautifulSoup

from .fingerprinting import compare_fingerprints
from .models import ExtractionRequest, PageClassification, TemplateMatch
from .services.template_service import TemplateService
from .templates import (
    BaseTemplateParser,
    GenericRuleTemplateParser,
)


class TemplateRegistry:
    def __init__(self, template_service: TemplateService | None = None) -> None:
        self.template_service = template_service or TemplateService()
        self.parsers: list[BaseTemplateParser] = []
        self.parsers_by_key = {parser.parser_key: parser for parser in self.parsers}

    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
        fingerprint=None,
    ) -> Tuple[Optional[TemplateMatch], Optional[BaseTemplateParser]]:
        manifest_match = self._match_manifest(classification, fingerprint)
        if manifest_match is not None:
            return manifest_match

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

    def _match_manifest(
        self,
        classification: PageClassification,
        fingerprint,
    ) -> Tuple[Optional[TemplateMatch], Optional[BaseTemplateParser]] | None:
        manifests = self.template_service.load_manifests()
        dsl_manifests = [manifest for manifest in manifests if manifest.extraction_plan is not None]
        legacy_manifests = [manifest for manifest in manifests if manifest.extraction_plan is None]

        preferred = self._select_best_manifest(dsl_manifests, classification, fingerprint)
        if preferred is None:
            preferred = self._select_best_manifest(legacy_manifests, classification, fingerprint)

        if preferred is None:
            return None

        best_manifest, best_score = preferred
        parser = None
        if best_manifest.extraction_plan is not None:
            parser = GenericRuleTemplateParser(best_manifest)
        elif best_manifest.parser_key in self.parsers_by_key:
            parser = self.parsers_by_key[best_manifest.parser_key]

        if parser is None:
            return None

        return (
            TemplateMatch(
                template_id=best_manifest.template_id,
                site_id=best_manifest.site_id,
                site_name=best_manifest.site_name,
                match_score=best_score,
                page_type=best_manifest.page_type,
                scenario=best_manifest.scenario,
                version=best_manifest.version,
            ),
            parser,
        )

    def _select_best_manifest(
        self,
        manifests,
        classification: PageClassification,
        fingerprint,
    ) -> tuple | None:
        best_manifest = None
        best_score = 0.0

        for manifest in manifests:
            if not manifest.active:
                continue
            if manifest.site_id != classification.site_id or manifest.scenario != classification.scenario:
                continue

            score = 0.0
            if manifest.fingerprint and fingerprint is not None:
                score = compare_fingerprints(fingerprint, manifest.fingerprint)
                if score < 0.8:
                    continue
            elif manifest.extraction_plan is not None:
                score = 0.81

            if score <= best_score:
                continue

            best_manifest = manifest
            best_score = score

        if best_manifest is None:
            return None
        return best_manifest, best_score
