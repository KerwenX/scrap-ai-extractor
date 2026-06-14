from __future__ import annotations

from typing import Iterable, Optional

from .extractors import BaseFallbackExtractor, ScrapeGraphFallbackExtractor
from .intent import parse_intent
from .logging_utils import get_logger
from .models import ExtractionRequest, ExtractionResponse
from .preprocessing import build_soup, clean_html, extract_page_title
from .template_registry import TemplateRegistry
from .validation import validate_data


class HybridExtractionEngine:
    def __init__(
        self,
        registry: Optional[TemplateRegistry] = None,
        fallback_extractor: Optional[BaseFallbackExtractor] = None,
    ) -> None:
        self.registry = registry or TemplateRegistry()
        self.fallback_extractor = fallback_extractor or ScrapeGraphFallbackExtractor()
        self.logger = get_logger(self.__class__.__name__)

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        logger_extra = {"request_id": request.request_id}
        self.logger.info("Starting extraction", extra=logger_extra)

        cleaned_html = clean_html(request.raw_html)
        request = request.model_copy(update={"raw_html": cleaned_html})
        soup = build_soup(cleaned_html)
        title = extract_page_title(soup)
        intent = parse_intent(request.user_prompt)

        match, parser = self.registry.match(request, soup, title)
        debug_trace = {
            "page_title": title,
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
        return ["result"]
