from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .fingerprinting import compare_fingerprints
from .models import ExtractionIntent, ExtractionRequest, PageClassification, TemplateMatch, TemplateManifest
from .preprocessing import normalize_text
from .rule_runtime import RuleRuntime
from .services.template_service import TemplateService
from .templates import BaseTemplateParser, GenericRuleTemplateParser
from .validation import validate_data


@dataclass
class TemplateIndex:
    by_site: dict[str, list[TemplateManifest]] = field(default_factory=dict)
    by_site_url_hash: dict[tuple[str, str], list[TemplateManifest]] = field(default_factory=dict)
    by_site_scenario: dict[tuple[str, str], list[TemplateManifest]] = field(default_factory=dict)
    by_scenario: dict[str, list[TemplateManifest]] = field(default_factory=dict)
    by_dom_signature: dict[str, list[TemplateManifest]] = field(default_factory=dict)
    by_template_id: dict[str, TemplateManifest] = field(default_factory=dict)
    active_manifests: list[TemplateManifest] = field(default_factory=list)


class TemplateRegistry:
    CHEAP_TOP_K = 5
    EXACT_URL_MATCH_LIMIT = 8

    def __init__(self, template_service: TemplateService | None = None) -> None:
        self.template_service = template_service or TemplateService()
        self.parsers: list[BaseTemplateParser] = []
        self.parsers_by_key = {parser.parser_key: parser for parser in self.parsers}
        self._rule_runtime = RuleRuntime()
        self._dsl_parser_cache: dict[str, GenericRuleTemplateParser] = {}
        self._index_cache: TemplateIndex | None = None
        self._index_token: tuple | None = None

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
        if not manifests:
            return None

        index = self._get_index(manifests)
        page_context = self._rule_runtime.build_page_context(soup)
        selection = self._select_best_manifest(
            index=index,
            request=request,
            classification=classification,
            fingerprint=fingerprint,
            page_context=page_context,
        )
        if selection is None:
            return None

        best_manifest, best_score, diagnostics = selection
        parser = self._get_parser(best_manifest)
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

    def _get_index(self, manifests: list[TemplateManifest]) -> TemplateIndex:
        token = tuple(
            (
                manifest.template_id,
                manifest.site_id,
                manifest.scenario,
                manifest.page_type,
                manifest.url_pattern_hash,
                manifest.active,
                manifest.lifecycle_status,
            )
            for manifest in manifests
        )
        if self._index_cache is not None and token == self._index_token:
            return self._index_cache

        index = TemplateIndex()
        for manifest in manifests:
            index.by_template_id[manifest.template_id] = manifest
            if not manifest.active or manifest.lifecycle_status != "active":
                continue
            index.active_manifests.append(manifest)
            site_family = self._site_family(manifest.site_id)
            if site_family:
                index.by_site.setdefault(site_family, []).append(manifest)
                if manifest.url_pattern_hash:
                    index.by_site_url_hash.setdefault((site_family, manifest.url_pattern_hash), []).append(manifest)
                if manifest.scenario:
                    index.by_site_scenario.setdefault((site_family, manifest.scenario), []).append(manifest)
            if manifest.scenario:
                index.by_scenario.setdefault(manifest.scenario, []).append(manifest)
            if manifest.fingerprint and manifest.fingerprint.dom_signature:
                index.by_dom_signature.setdefault(manifest.fingerprint.dom_signature, []).append(manifest)

        self._index_cache = index
        self._index_token = token
        return index

    def _select_best_manifest(
        self,
        index: TemplateIndex,
        request: ExtractionRequest,
        classification: PageClassification,
        fingerprint,
        page_context,
    ) -> tuple | None:
        candidates = self._recall_candidates(index, request, classification, fingerprint)
        if not candidates:
            return None

        cheap_ranked = sorted(
            candidates,
            key=lambda manifest: self._cheap_score_manifest(manifest, request, classification, fingerprint),
            reverse=True,
        )
        expensive_candidates = cheap_ranked[: self.CHEAP_TOP_K]

        best_manifest = None
        best_score = 0.0
        best_diagnostics: dict[str, float] | None = None

        for manifest in expensive_candidates:
            diagnostics = self._score_manifest(
                manifest=manifest,
                request=request,
                classification=classification,
                fingerprint=fingerprint,
                page_context=page_context,
            )
            score = diagnostics["match_score"]
            if score <= best_score:
                continue
            best_manifest = manifest
            best_score = score
            best_diagnostics = diagnostics
            if self._should_early_exit(diagnostics):
                break

        if best_manifest is None:
            return None
        return best_manifest, best_score, best_diagnostics or {}

    def _recall_candidates(
        self,
        index: TemplateIndex,
        request: ExtractionRequest,
        classification: PageClassification,
        fingerprint,
    ) -> list[TemplateManifest]:
        site_family = self._site_family(classification.site_id)
        request_url_hash = self.template_service.build_url_pattern_hash_for_url(request.url) if request.url else ""
        results: list[TemplateManifest] = []
        seen: set[str] = set()

        def extend(items: list[TemplateManifest] | None) -> None:
            if not items:
                return
            for item in items:
                if item.template_id in seen:
                    continue
                seen.add(item.template_id)
                results.append(item)

        if request.url and site_family:
            exact = index.by_site_url_hash.get((site_family, request_url_hash), [])
            if exact and len(exact) <= self.EXACT_URL_MATCH_LIMIT:
                return list(exact)
            extend(exact)
            extend(index.by_site_scenario.get((site_family, classification.scenario), []))
            extend(index.by_site.get(site_family, []))
            if results:
                return results

        if not request.url:
            if classification.scenario and classification.scenario != "unknown":
                extend(index.by_scenario.get(classification.scenario, []))
            if fingerprint is not None and getattr(fingerprint, "dom_signature", ""):
                extend(index.by_dom_signature.get(fingerprint.dom_signature, []))
            if results:
                return results

        if site_family:
            extend(index.by_site.get(site_family, []))
        if classification.scenario and classification.scenario != "unknown":
            extend(index.by_scenario.get(classification.scenario, []))
        if fingerprint is not None and getattr(fingerprint, "dom_signature", ""):
            extend(index.by_dom_signature.get(fingerprint.dom_signature, []))
        extend(index.active_manifests)
        return results

    def _cheap_score_manifest(
        self,
        manifest: TemplateManifest,
        request: ExtractionRequest,
        classification: PageClassification,
        fingerprint,
    ) -> float:
        fingerprint_score = 0.0
        if manifest.fingerprint and fingerprint is not None:
            fingerprint_score = compare_fingerprints(fingerprint, manifest.fingerprint)
        classification_affinity = self._classification_affinity(manifest, classification)
        site_affinity = self._site_affinity(manifest.site_id, classification.site_id)
        url_pattern_affinity = self._url_pattern_affinity(manifest, request.url)
        score = (
            0.42 * classification_affinity
            + 0.28 * site_affinity
            + 0.2 * url_pattern_affinity
            + 0.1 * fingerprint_score
        )
        if manifest.extraction_plan is not None:
            score += 0.03
        return round(min(score, 1.0), 4)

    def _score_manifest(
        self,
        manifest: TemplateManifest,
        request: ExtractionRequest,
        classification: PageClassification,
        fingerprint,
        page_context,
    ) -> dict[str, float]:
        fingerprint_score = 0.0
        if manifest.fingerprint and fingerprint is not None:
            fingerprint_score = compare_fingerprints(fingerprint, manifest.fingerprint)

        classification_affinity = self._classification_affinity(manifest, classification)
        site_affinity = self._site_affinity(manifest.site_id, classification.site_id)
        url_pattern_affinity = self._url_pattern_affinity(manifest, request.url)

        if manifest.extraction_plan is None:
            if manifest.scenario != classification.scenario or fingerprint_score < 0.8:
                return self._score_payload(
                    0.0, fingerprint_score, 0.0, 0.0, classification_affinity, site_affinity, url_pattern_affinity
                )
            legacy_score = (
                0.65 * fingerprint_score
                + 0.20 * classification_affinity
                + 0.10 * site_affinity
                + 0.05 * url_pattern_affinity
            )
            return self._score_payload(
                legacy_score,
                fingerprint_score,
                0.0,
                0.0,
                classification_affinity,
                site_affinity,
                url_pattern_affinity,
            )

        parser = self._get_parser(manifest)
        extracted = parser.extract(
            request,
            page_context,
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

        return self._score_payload(
            score,
            fingerprint_score,
            selector_hit_rate,
            required_hit_rate,
            classification_affinity,
            site_affinity,
            url_pattern_affinity,
        )

    def _score_payload(
        self,
        score: float,
        fingerprint_score: float,
        selector_hit_rate: float,
        required_hit_rate: float,
        classification_affinity: float,
        site_affinity: float,
        url_pattern_affinity: float,
    ) -> dict[str, float]:
        return {
            "match_score": round(min(score, 1.0), 4),
            "fingerprint_score": round(fingerprint_score, 4),
            "selector_hit_rate": round(selector_hit_rate, 4),
            "required_hit_rate": round(required_hit_rate, 4),
            "classification_affinity": round(classification_affinity, 4),
            "site_affinity": round(site_affinity, 4),
            "url_pattern_affinity": round(url_pattern_affinity, 4),
        }

    def _should_early_exit(self, diagnostics: dict[str, float]) -> bool:
        return (
            diagnostics.get("url_pattern_affinity", 0.0) >= 1.0
            and diagnostics.get("classification_affinity", 0.0) >= 0.95
            and diagnostics.get("required_hit_rate", 0.0) >= 0.95
            and diagnostics.get("selector_hit_rate", 0.0) >= 0.95
            and diagnostics.get("fingerprint_score", 0.0) >= 0.9
        )

    def _get_parser(self, manifest: TemplateManifest) -> BaseTemplateParser | None:
        if manifest.extraction_plan is not None:
            cached = self._dsl_parser_cache.get(manifest.template_id)
            if cached is None:
                cached = GenericRuleTemplateParser(manifest, runtime=self._rule_runtime)
                self._dsl_parser_cache[manifest.template_id] = cached
            return cached
        return self.parsers_by_key.get(manifest.parser_key)

    def _selector_hit_rate(self, data: dict, manifest: TemplateManifest) -> float:
        total_fields = len(manifest.extraction_plan.fields) if manifest.extraction_plan else 0
        if total_fields == 0:
            return 0.0
        hit_count = 0
        for field in manifest.extraction_plan.fields:
            value = data.get(field.field_name)
            if self._has_value(value):
                hit_count += 1
        return hit_count / total_fields

    def _classification_affinity(self, manifest: TemplateManifest, classification: PageClassification) -> float:
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

    def _url_pattern_affinity(self, manifest: TemplateManifest, request_url: str) -> float:
        if not request_url or not manifest.url_pattern_hash:
            return 0.0
        request_hash = self.template_service.build_url_pattern_hash_for_url(request_url)
        if not request_hash:
            return 0.0
        return 1.0 if manifest.url_pattern_hash == request_hash else 0.0
