from __future__ import annotations

from typing import Optional, Tuple

from bs4 import BeautifulSoup

from .fingerprinting import compare_fingerprints
from .models import ExtractionIntent, ExtractionRequest, PageClassification, TemplateMatch
from .preprocessing import normalize_text
from .validation import validate_data
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
        manifest_match = self._match_manifest(request, soup, classification, fingerprint)
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
        request: ExtractionRequest,
        soup: BeautifulSoup,
        classification: PageClassification,
        fingerprint,
    ) -> Tuple[Optional[TemplateMatch], Optional[BaseTemplateParser]] | None:
        manifests = self.template_service.load_manifests()
        dsl_manifests = [manifest for manifest in manifests if manifest.extraction_plan is not None]
        legacy_manifests = [manifest for manifest in manifests if manifest.extraction_plan is None]

        preferred = self._select_best_manifest(
            dsl_manifests,
            request,
            soup,
            classification,
            fingerprint,
        )
        if preferred is None:
            preferred = self._select_best_manifest(
                legacy_manifests,
                request,
                soup,
                classification,
                fingerprint,
            )

        if preferred is None:
            return None

        best_manifest, best_score, diagnostics = preferred
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
                fingerprint_score=diagnostics.get("fingerprint_score", 0.0),
                selector_hit_rate=diagnostics.get("selector_hit_rate", 0.0),
                required_hit_rate=diagnostics.get("required_hit_rate", 0.0),
                classification_affinity=diagnostics.get("classification_affinity", 0.0),
                score_breakdown=diagnostics,
            ),
            parser,
        )

    def _select_best_manifest(
        self,
        manifests,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        classification: PageClassification,
        fingerprint,
    ) -> tuple | None:
        best_manifest = None
        best_score = 0.0
        best_diagnostics: dict[str, float] | None = None

        for manifest in manifests:
            if not manifest.active or manifest.lifecycle_status != "active":
                continue
            if manifest.site_id != classification.site_id:
                continue

            diagnostics = self._score_manifest(
                manifest,
                request,
                soup,
                classification,
                fingerprint,
            )
            score = diagnostics["match_score"]
            if score <= 0:
                continue

            if score <= best_score:
                continue

            best_manifest = manifest
            best_score = score
            best_diagnostics = diagnostics

        if best_manifest is None:
            return None
        return best_manifest, best_score, best_diagnostics or {}

    def _score_manifest(
        self,
        manifest,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        classification: PageClassification,
        fingerprint,
    ) -> dict[str, float]:
        fingerprint_score = 0.0
        if manifest.fingerprint and fingerprint is not None:
            fingerprint_score = compare_fingerprints(fingerprint, manifest.fingerprint)

        classification_affinity = self._classification_affinity(manifest, classification)

        if manifest.extraction_plan is None:
            if manifest.scenario != classification.scenario:
                return {
                    "match_score": 0.0,
                    "fingerprint_score": fingerprint_score,
                    "selector_hit_rate": 0.0,
                    "required_hit_rate": 0.0,
                    "classification_affinity": classification_affinity,
                }
            if fingerprint_score < 0.8:
                return {
                    "match_score": 0.0,
                    "fingerprint_score": fingerprint_score,
                    "selector_hit_rate": 0.0,
                    "required_hit_rate": 0.0,
                    "classification_affinity": classification_affinity,
                }
            return {
                "match_score": round(0.75 * fingerprint_score + 0.25 * classification_affinity, 4),
                "fingerprint_score": round(fingerprint_score, 4),
                "selector_hit_rate": 0.0,
                "required_hit_rate": 0.0,
                "classification_affinity": round(classification_affinity, 4),
            }

        parser = GenericRuleTemplateParser(manifest)
        extracted = parser.extract(
            request,
            soup,
            intent=ExtractionIntent(normalized_prompt=request.user_prompt),
        ).data
        selector_hit_rate = self._selector_hit_rate(extracted, manifest)
        validation = validate_data(extracted, manifest.required_fields)
        required_hit_rate = validation.coverage

        score = (
            0.5 * required_hit_rate
            + 0.25 * selector_hit_rate
            + 0.15 * fingerprint_score
            + 0.10 * classification_affinity
        )
        if selector_hit_rate >= 0.85 and required_hit_rate >= 0.85:
            score += 0.08
        elif validation.passed and selector_hit_rate >= 0.6:
            score += 0.04

        if not validation.passed and selector_hit_rate < 0.5:
            score = 0.0
        elif selector_hit_rate < 0.35:
            score = 0.0

        return {
            "match_score": round(min(score, 1.0), 4),
            "fingerprint_score": round(fingerprint_score, 4),
            "selector_hit_rate": round(selector_hit_rate, 4),
            "required_hit_rate": round(required_hit_rate, 4),
            "classification_affinity": round(classification_affinity, 4),
        }

    def _selector_hit_rate(self, data: dict, manifest) -> float:
        total_fields = len(manifest.extraction_plan.fields) if manifest.extraction_plan else 0
        if total_fields == 0:
            return 0.0
        hit_count = 0
        for field in manifest.extraction_plan.fields:
            value = data.get(field.field_name)
            if self._has_value(value):
                hit_count += 1
        return hit_count / total_fields

    def _classification_affinity(self, manifest, classification: PageClassification) -> float:
        score = 0.1
        if manifest.scenario == classification.scenario:
            score += 0.6
        elif "unknown" in {manifest.scenario, classification.scenario}:
            score += 0.25

        if manifest.page_type == classification.page_type:
            score += 0.4
        elif "unknown" in {manifest.page_type, classification.page_type}:
            score += 0.15

        return min(score, 1.0)

    def _has_value(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(normalize_text(value))
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return True
