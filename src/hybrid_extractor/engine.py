from __future__ import annotations

from typing import Iterable, Optional

from .classification import PageClassifier
from .extractors import BaseFallbackExtractor, ScrapeGraphFallbackExtractor
from .fingerprinting import build_fingerprint
from .intent import parse_intent
from .logging_utils import get_logger
from .models import (
    ExtractionPlan,
    ExtractionRequest,
    ExtractionResponse,
    FieldRule,
    FieldSelectorRule,
    PostProcessStep,
    TemplateCandidate,
    TemplateManifest,
)
from .preprocessing import build_soup, clean_html, extract_page_title
from .services.template_service import TemplateService
from .template_registry import TemplateRegistry
from .validation import validate_data


class HybridExtractionEngine:
    def __init__(
        self,
        registry: Optional[TemplateRegistry] = None,
        fallback_extractor: Optional[BaseFallbackExtractor] = None,
        classifier: Optional[PageClassifier] = None,
        template_service: Optional[TemplateService] = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.registry = registry or TemplateRegistry(template_service=self.template_service)
        self.fallback_extractor = fallback_extractor or ScrapeGraphFallbackExtractor()
        self.classifier = classifier or PageClassifier()
        self.logger = get_logger(self.__class__.__name__)

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        logger_extra = {"request_id": request.request_id}
        self.logger.info("Starting extraction", extra=logger_extra)

        cleaned_html = clean_html(request.raw_html)
        request = request.model_copy(update={"raw_html": cleaned_html})
        soup = build_soup(cleaned_html)
        title = extract_page_title(soup)
        intent = parse_intent(request.user_prompt)
        classification = self.classifier.classify(request, soup)
        fingerprint = build_fingerprint(soup)

        match, parser = self.registry.match(
            request, soup, title, classification, fingerprint=fingerprint
        )
        debug_trace = {
            "page_title": title,
            "classification": classification.model_dump(),
            "fingerprint": fingerprint.model_dump(),
            "template_match": match.model_dump() if match else None,
            "intent": intent.model_dump(),
        }

        required_fields = self._required_fields(intent)
        drift_detected = False

        if parser and match:
            self.logger.info(
                "Using deterministic parser %s", parser.template_id, extra=logger_extra
            )
            deterministic_result = parser.extract(request, soup, intent)
            validation = validate_data(deterministic_result.data, required_fields)
            debug_trace["deterministic_validation"] = validation.model_dump()

            if validation.passed:
                stored_manifest_path = None
                existing_manifest = self.template_service.get_manifest(match.template_id)
                if existing_manifest is None or existing_manifest.fingerprint is None:
                    manifest = TemplateManifest(
                        template_id=match.template_id,
                        parser_key=parser.parser_key,
                        site_id=match.site_id,
                        site_name=match.site_name,
                        page_type=match.page_type,
                        scenario=match.scenario,
                        version=match.version,
                        fingerprint=fingerprint,
                        required_fields=list(required_fields),
                        notes="Auto-captured from a successful deterministic parsing run.",
                    )
                    stored_manifest_path = str(self.template_service.upsert_manifest(manifest))
                    debug_trace["template_manifest_path"] = stored_manifest_path

                self.logger.info("Deterministic parsing passed validation", extra=logger_extra)
                return ExtractionResponse(
                    request_id=request.request_id,
                    status="success",
                    template_id=match.template_id,
                    page_type=match.page_type,
                    extractor_type="deterministic",
                    confidence=round(0.7 + 0.3 * validation.coverage, 3),
                    drift_detected=False,
                    data=deterministic_result.data,
                    validation_report=validation,
                    debug_trace=debug_trace,
                )

            drift_detected = True
            self.logger.info(
                "Deterministic parsing failed validation; falling back to LLM",
                extra=logger_extra,
            )

        llm_result = self.fallback_extractor.extract(request, intent)
        llm_validation = validate_data(llm_result.data, required_fields)
        debug_trace["llm_validation"] = llm_validation.model_dump()
        candidate_path = None

        if llm_validation.passed:
            candidate = TemplateCandidate(
                request_id=request.request_id,
                site_id=classification.site_id,
                site_name=classification.site_name,
                page_type=classification.page_type,
                scenario=classification.scenario,
                user_prompt=request.user_prompt,
                source_url=request.url,
                fingerprint=fingerprint,
                extracted_fields=sorted(llm_result.data.keys()),
                sample_data=dict(list(llm_result.data.items())[:8]),
                proposed_plan=self._build_candidate_plan(soup, llm_result.data),
            )
            candidate_path = str(self.template_service.persist_candidate(candidate))
            debug_trace["template_candidate_path"] = candidate_path

        status = "success" if llm_validation.passed else "failed"
        extractor_type = "hybrid" if parser and match else "llm"
        template_id = match.template_id if match else None
        page_type = match.page_type if match else intent.entity_type

        self.logger.info("LLM fallback finished with status=%s", status, extra=logger_extra)
        return ExtractionResponse(
            request_id=request.request_id,
            status=status,
            template_id=template_id,
            page_type=page_type,
            extractor_type=extractor_type,
            confidence=round(0.55 + 0.35 * llm_validation.coverage, 3),
            drift_detected=drift_detected,
            data=llm_result.data,
            validation_report=llm_validation,
            debug_trace=debug_trace,
        )

    def _required_fields(self, intent) -> Iterable[str]:
        if intent.entity_type == "disease_page":
            return ["name", "summary", "symptoms", "treatment"]
        if intent.entity_type == "qa_page":
            return ["summary"]
        return ["result"]

    def _build_candidate_plan(self, soup, data: dict) -> ExtractionPlan | None:
        if not data:
            return None
        field_rules: list[FieldRule] = []

        if "name" in data and soup.find("h1"):
            field_rules.append(
                FieldRule(
                    field_name="name",
                    selectors=[FieldSelectorRule(kind="css", value="h1")],
                    postprocess=[PostProcessStep(op="strip")],
                )
            )

        if "summary" in data and soup.find("meta", attrs={"name": "description"}):
            field_rules.append(
                FieldRule(
                    field_name="summary",
                    selectors=[FieldSelectorRule(kind="meta", value="description")],
                    postprocess=[PostProcessStep(op="strip")],
                )
            )

        section_names = {
            "causes": "\u75c5\u56e0",
            "symptoms": "\u75c7\u72b6",
            "diagnosis": "\u8bca\u65ad",
            "treatment": "\u6cbb\u7597",
            "prevention": "\u9884\u9632",
        }
        tab_text = soup.get_text(" ", strip=True)
        for field_name, section_title in section_names.items():
            if field_name not in data:
                continue
            if section_title not in tab_text:
                continue
            field_rules.append(
                FieldRule(
                    field_name=field_name,
                    selectors=[FieldSelectorRule(kind="section_tab", value=section_title)],
                    postprocess=[PostProcessStep(op="strip")],
                )
            )

        if not field_rules:
            return None

        return ExtractionPlan(mode="declarative", fields=field_rules)
