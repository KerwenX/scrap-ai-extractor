from __future__ import annotations

from typing import Optional, Tuple
from urllib.parse import urlparse

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

        classification_site_family = self._site_family(classification.site_id)
        request_url_hash = self.template_service.build_url_pattern_hash_for_url(request.url) if request.url else ""
        should_filter_by_site = bool(
            classification.site_id
            and classification.site_id != "unknown"
        )

        same_site_manifests = []
        for manifest in manifests:
            if not manifest.active or manifest.lifecycle_status != "active":
                continue
            if should_filter_by_site and not self._site_matches(
                manifest.site_id,
                classification.site_id,
                classification_site_family,
            ):
                continue
            same_site_manifests.append(manifest)

        prioritized_manifests = self._prioritize_by_url_pattern(same_site_manifests, request_url_hash)

        for manifest in prioritized_manifests:
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
        site_affinity = self._site_affinity(manifest.site_id, classification.site_id)
        url_pattern_affinity = self._url_pattern_affinity(manifest, request.url)

        if manifest.extraction_plan is None:
            if manifest.scenario != classification.scenario:
                return {
                    "match_score": 0.0,
                    "fingerprint_score": fingerprint_score,
                    "selector_hit_rate": 0.0,
                    "required_hit_rate": 0.0,
                    "classification_affinity": classification_affinity,
                    "site_affinity": site_affinity,
                    "url_pattern_affinity": url_pattern_affinity,
                }
            if fingerprint_score < 0.8:
                return {
                    "match_score": 0.0,
                    "fingerprint_score": fingerprint_score,
                    "selector_hit_rate": 0.0,
                    "required_hit_rate": 0.0,
                    "classification_affinity": classification_affinity,
                    "site_affinity": site_affinity,
                    "url_pattern_affinity": url_pattern_affinity,
                }
            return {
                "match_score": round(
                    0.65 * fingerprint_score
                    + 0.20 * classification_affinity
                    + 0.10 * site_affinity
                    + 0.05 * url_pattern_affinity,
                    4,
                ),
                "fingerprint_score": round(fingerprint_score, 4),
                "selector_hit_rate": 0.0,
                "required_hit_rate": 0.0,
                "classification_affinity": round(classification_affinity, 4),
                "site_affinity": round(site_affinity, 4),
                "url_pattern_affinity": round(url_pattern_affinity, 4),
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
            0.42 * required_hit_rate
            + 0.22 * selector_hit_rate
            + 0.15 * fingerprint_score
            + 0.11 * classification_affinity
            + 0.07 * site_affinity
            + 0.03 * url_pattern_affinity
        )
        if selector_hit_rate >= 0.85 and required_hit_rate >= 0.85:
            score += 0.08
        elif validation.passed and selector_hit_rate >= 0.6:
            score += 0.04

        if manifest.fingerprint is not None and classification_affinity < 0.3 and fingerprint_score < 0.3:
            score = 0.0
        elif manifest.fingerprint is None and classification_affinity < 0.3 and selector_hit_rate < 0.9:
            score = 0.0
        elif not validation.passed and selector_hit_rate < 0.5:
            score = 0.0
        elif selector_hit_rate < 0.35:
            score = 0.0

        return {
            "match_score": round(min(score, 1.0), 4),
            "fingerprint_score": round(fingerprint_score, 4),
            "selector_hit_rate": round(selector_hit_rate, 4),
            "required_hit_rate": round(required_hit_rate, 4),
            "classification_affinity": round(classification_affinity, 4),
            "site_affinity": round(site_affinity, 4),
            "url_pattern_affinity": round(url_pattern_affinity, 4),
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

    def _site_matches(
        self,
        manifest_site_id: str,
        request_site_id: str,
        request_site_family: str = "",
    ) -> bool:
        if manifest_site_id == request_site_id:
            return True
        if not manifest_site_id or not request_site_id:
            return False
        return self._site_family(manifest_site_id) == (request_site_family or self._site_family(request_site_id))

    def _site_affinity(self, manifest_site_id: str, request_site_id: str) -> float:
        if manifest_site_id == request_site_id:
            return 1.0
        if not manifest_site_id or not request_site_id:
            return 0.0
        if self._site_family(manifest_site_id) == self._site_family(request_site_id):
            return 0.85
        return 0.0

    def _site_family(self, site_id: str) -> str:
        site_id = (site_id or "").strip().lower()
        if not site_id or site_id == "unknown":
            return ""

        host = urlparse(f"https://{site_id}").netloc or site_id
        if host.startswith("www."):
            host = host[4:]

        parts = [part for part in host.split(".") if part]
        if len(parts) <= 2:
            return host
        if len(parts[-1]) == 2 and len(parts[-2]) <= 3:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])

    def _prioritize_by_url_pattern(self, manifests, request_url_hash: str):
        if not request_url_hash:
            return list(manifests)

        exact = [manifest for manifest in manifests if manifest.url_pattern_hash == request_url_hash]
        if exact:
            others = [manifest for manifest in manifests if manifest.url_pattern_hash != request_url_hash]
            return exact + others
        return list(manifests)

    def _url_pattern_affinity(self, manifest, request_url: str) -> float:
        if not request_url or not manifest.url_pattern_hash:
            return 0.0
        request_hash = self.template_service.build_url_pattern_hash_for_url(request_url)
        if not request_hash:
            return 0.0
        return 1.0 if manifest.url_pattern_hash == request_hash else 0.0
