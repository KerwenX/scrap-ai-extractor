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
    TemplateAnalysis,
    TemplateCandidate,
    TemplateFieldAnalysis,
    TemplateManifest,
)
from .preprocessing import build_soup, clean_html, extract_page_title, normalize_text
from .prompts import (
    PROMPT_VERSION,
    build_template_analysis_prompt,
    build_template_plan_prompt,
)
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
            "prompt_version": PROMPT_VERSION,
        }

        required_fields = self._required_fields(match)
        drift_detected = False

        if parser and match:
            self.logger.info(
                "Using deterministic parser %s", parser.template_id, extra=logger_extra
            )
            deterministic_result = parser.extract(request, soup, intent)
            validation = validate_data(deterministic_result.data, required_fields)
            debug_trace["deterministic_validation"] = validation.model_dump()
            manifest = self.template_service.get_manifest(match.template_id)
            drift_report = self._build_drift_report(
                match.match_score,
                validation.coverage,
                validation.passed,
                has_fingerprint=bool(manifest and manifest.fingerprint),
                is_dsl_template=bool(manifest and manifest.extraction_plan is not None),
            )
            debug_trace["drift_report"] = drift_report

            if validation.passed and not drift_report["should_fallback"]:
                stored_manifest_path = None
                existing_manifest = manifest
                if existing_manifest is None or existing_manifest.fingerprint is None:
                    if existing_manifest is not None:
                        manifest = existing_manifest.model_copy(
                            update={
                                "fingerprint": fingerprint,
                                "required_fields": list(required_fields)
                                or existing_manifest.required_fields,
                                "notes": (
                                    existing_manifest.notes
                                    or "Auto-captured from a successful deterministic parsing run."
                                ),
                            }
                        )
                    else:
                        extraction_plan = getattr(getattr(parser, "manifest", None), "extraction_plan", None)
                        template_key = getattr(getattr(parser, "manifest", None), "template_key", "")
                        source_candidate_id = getattr(
                            getattr(parser, "manifest", None), "source_candidate_id", None
                        )
                        manifest = TemplateManifest(
                            template_id=match.template_id,
                            parser_key=parser.parser_key,
                            site_id=match.site_id,
                            site_name=match.site_name,
                            page_type=match.page_type,
                            scenario=match.scenario,
                            version=match.version,
                            template_key=template_key,
                            lifecycle_status="active",
                            fingerprint=fingerprint,
                            required_fields=list(required_fields),
                            extraction_plan=extraction_plan,
                            notes="Auto-captured from a successful deterministic parsing run.",
                            source_candidate_id=source_candidate_id,
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
                    drift_detected=drift_report["drift_detected"],
                    data=deterministic_result.data,
                    validation_report=validation,
                    debug_trace=debug_trace,
                )

            drift_detected = drift_report["drift_detected"]
            self.logger.info(
                "Deterministic parsing requested fallback; reason=%s",
                drift_report["reason"],
                extra=logger_extra,
            )

        llm_result = self.fallback_extractor.extract(request, intent)
        candidate_seed_data = self._prepare_candidate_seed_data(llm_result.data)
        normalized_llm_data = candidate_seed_data if candidate_seed_data else llm_result.data
        llm_validation = validate_data(normalized_llm_data, required_fields)
        debug_trace["llm_validation"] = llm_validation.model_dump()
        candidate_path = None
        solidified_manifest = None

        if llm_validation.passed:
            analysis = self._build_candidate_analysis(soup, candidate_seed_data)
            proposed_plan = self._build_candidate_plan(soup, candidate_seed_data, analysis)
            candidate = TemplateCandidate(
                request_id=request.request_id,
                site_id=classification.site_id,
                site_name=classification.site_name,
                page_type=classification.page_type,
                scenario=classification.scenario,
                user_prompt=request.user_prompt,
                source_url=request.url,
                fingerprint=fingerprint,
                extracted_fields=sorted(candidate_seed_data.keys()),
                sample_data=dict(list(candidate_seed_data.items())[:8]),
                analysis=analysis,
                proposed_plan=proposed_plan,
            )
            candidate_path = str(self.template_service.persist_candidate(candidate))
            debug_trace["template_candidate_path"] = candidate_path
            debug_trace["template_analysis"] = analysis.model_dump() if analysis else None
            debug_trace["template_analysis_prompt"] = build_template_analysis_prompt(
                request.user_prompt, sorted(candidate_seed_data.keys())
            )
            debug_trace["template_plan_prompt"] = build_template_plan_prompt(
                request.user_prompt, sorted(candidate_seed_data.keys())
            )
            solidified_manifest = self.template_service.solidify_candidate(
                candidate,
                list(required_fields),
            )
            if solidified_manifest is not None:
                debug_trace["solidified_template_id"] = solidified_manifest.template_id
                debug_trace["solidified_template_path"] = str(
                    self.template_service.template_store_dir
                    / f"{solidified_manifest.template_id}.json"
                )

        status = "success" if llm_validation.passed else "failed"
        extractor_type = "hybrid" if parser and match else "llm"
        template_id = (
            match.template_id
            if match
            else solidified_manifest.template_id if solidified_manifest else None
        )
        page_type = (
            match.page_type
            if match
            else solidified_manifest.page_type if solidified_manifest else intent.entity_type
        )

        self.logger.info("LLM fallback finished with status=%s", status, extra=logger_extra)
        return ExtractionResponse(
            request_id=request.request_id,
            status=status,
            template_id=template_id,
            page_type=page_type,
            extractor_type=extractor_type,
            confidence=round(0.55 + 0.35 * llm_validation.coverage, 3),
            drift_detected=drift_detected,
            data=normalized_llm_data,
            validation_report=llm_validation,
            debug_trace=debug_trace,
        )

    def _required_fields(self, match) -> Iterable[str]:
        if not match:
            return []
        manifest = self.template_service.get_manifest(match.template_id)
        if manifest is None:
            return []
        return manifest.required_fields

    def _build_drift_report(
        self,
        match_score: float,
        validation_coverage: float,
        validation_passed: bool,
        has_fingerprint: bool,
        is_dsl_template: bool = False,
    ) -> dict:
        if not validation_passed:
            return {
                "drift_detected": True,
                "should_fallback": True,
                "level": "high",
                "reason": "validation_failed",
                "fingerprint_score": match_score,
                "validation_coverage": validation_coverage,
            }
        if not has_fingerprint:
            return {
                "drift_detected": False,
                "should_fallback": False,
                "level": "none",
                "reason": "no_baseline_fingerprint",
                "fingerprint_score": match_score,
                "validation_coverage": validation_coverage,
            }
        if is_dsl_template:
            if match_score < 0.45:
                return {
                    "drift_detected": True,
                    "should_fallback": False,
                    "level": "medium",
                    "reason": "fingerprint_similarity_low_but_valid_dsl",
                    "fingerprint_score": match_score,
                    "validation_coverage": validation_coverage,
                }
            return {
                "drift_detected": False,
                "should_fallback": False,
                "level": "none",
                "reason": "stable_valid_dsl",
                "fingerprint_score": match_score,
                "validation_coverage": validation_coverage,
            }
        if match_score < 0.81:
            return {
                "drift_detected": True,
                "should_fallback": True,
                "level": "high",
                "reason": "fingerprint_similarity_low",
                "fingerprint_score": match_score,
                "validation_coverage": validation_coverage,
            }
        return {
            "drift_detected": False,
            "should_fallback": False,
            "level": "none",
            "reason": "stable",
            "fingerprint_score": match_score,
            "validation_coverage": validation_coverage,
        }

    def _build_candidate_analysis(self, soup, data: dict) -> TemplateAnalysis | None:
        if not data:
            return None

        page_cues: list[str] = []
        if soup.find("h1"):
            page_cues.append("page has h1 heading")
        if soup.find("meta", attrs={"name": "description"}):
            page_cues.append("page has description meta")
        if len(self._build_section_tab_map(soup)) >= 2:
            page_cues.append("page has tabbed sections")
        if len(soup.find_all(["h2", "h3"])) >= 2:
            page_cues.append("page has repeated section headings")

        field_analyses: list[TemplateFieldAnalysis] = []
        fallback_fields: list[str] = []

        for field_name, value in data.items():
            selector_candidates = self._infer_selector_candidates(soup, field_name, value)
            likely_anchors = [f"{rule.kind}:{rule.value}" for rule in selector_candidates]
            if likely_anchors:
                feasibility = "high"
            elif isinstance(value, list) and value:
                feasibility = "medium"
            else:
                feasibility = "low"
                fallback_fields.append(field_name)

            field_analyses.append(
                TemplateFieldAnalysis(
                    field_name=field_name,
                    value_type=self._infer_value_type(value),
                    likely_anchors=likely_anchors,
                    extraction_notes=(
                        "deterministic anchor available"
                        if likely_anchors
                        else "no stable deterministic anchor identified in generic heuristic phase"
                    ),
                    deterministic_feasibility=feasibility,
                )
            )

        return TemplateAnalysis(
            summary="Heuristic template analysis generated from one successful fallback extraction.",
            page_cues=page_cues,
            field_analyses=field_analyses,
            fallback_fields=sorted(set(fallback_fields)),
        )

    def _build_candidate_plan(
        self, soup, data: dict, analysis: TemplateAnalysis | None = None
    ) -> ExtractionPlan | None:
        if not data:
            return None
        field_rules: list[FieldRule] = []

        for field_name, value in data.items():
            selectors = self._infer_selector_candidates(soup, field_name, value)
            if not selectors:
                continue
            postprocess = [PostProcessStep(op="strip")]
            field_rules.append(
                FieldRule(field_name=field_name, selectors=selectors, postprocess=postprocess)
            )

        if analysis:
            supported_fields = {
                item.field_name
                for item in analysis.field_analyses
                if item.deterministic_feasibility in {"high", "medium"}
            }
            field_rules = [rule for rule in field_rules if rule.field_name in supported_fields]

        if not field_rules:
            return None

        return ExtractionPlan(mode="declarative", fields=field_rules)

    def _prepare_candidate_seed_data(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return {}
        if len(data) == 1:
            wrapper_key = next(iter(data.keys()))
            wrapper_value = data.get(wrapper_key)
            if wrapper_key in {"content", "result", "data"} and isinstance(wrapper_value, dict):
                scalar_children = {
                    key: value
                    for key, value in wrapper_value.items()
                    if isinstance(value, (str, list, dict))
                }
                if scalar_children:
                    return scalar_children
        return data

    def _infer_value_type(self, value) -> str:
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "object"
        return "unknown"

    def _infer_selector_candidates(self, soup, field_name: str, value) -> list[FieldSelectorRule]:
        selectors: list[FieldSelectorRule] = []

        label_selector = self._infer_label_selector_by_field_name(soup, field_name)
        if label_selector is not None:
            selectors.append(label_selector)

        selector = self._infer_single_selector(soup, field_name, value)
        if selector and not any(
            existing.kind == selector.kind and existing.value == selector.value for existing in selectors
        ):
            selectors.append(selector)

        return selectors

    def _infer_single_selector(self, soup, field_name: str, value) -> FieldSelectorRule | None:
        label_selector = self._infer_label_selector_by_field_name(soup, field_name)
        if label_selector is not None:
            return label_selector
        scalar = self._to_scalar_text(value)
        if not scalar:
            return None

        h1 = soup.find("h1")
        if h1 and normalize_text(h1.get_text(" ", strip=True)) == scalar:
            return FieldSelectorRule(kind="css", value="h1")

        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and normalize_text(meta_description.get("content", "")) == scalar:
            return FieldSelectorRule(kind="meta", value="description")

        tab_title = self._match_tabbed_section(soup, scalar)
        if tab_title:
            return FieldSelectorRule(kind="section_tab", value=tab_title)

        node = self._find_text_node(soup, scalar)
        if node is None:
            return None

        label_selector = self._build_label_value_selector(node, scalar)
        if label_selector is not None:
            return label_selector

        if node.get("id"):
            return FieldSelectorRule(kind="id", value=node.get("id"))

        selector = self._build_css_selector(node, soup)
        if selector:
            return FieldSelectorRule(kind="css", value=selector)
        return None

    def _infer_label_selector_by_field_name(
        self, soup, field_name: str
    ) -> FieldSelectorRule | None:
        normalized_field_name = normalize_text(field_name)
        if not normalized_field_name:
            return None

        label_aliases = {
            normalized_field_name,
            normalized_field_name.rstrip("：:"),
            f"{normalized_field_name}：",
            f"{normalized_field_name}:",
        }

        for node in soup.find_all(["td", "th", "dt", "dd", "span", "div", "label", "strong", "b"]):
            node_text = normalize_text(node.get_text(" ", strip=True))
            compact_text = node_text.replace(" ", "")
            if compact_text in {alias.replace(" ", "") for alias in label_aliases}:
                return FieldSelectorRule(kind="label_value", value=normalized_field_name)
        return None

    def _to_scalar_text(self, value) -> str:
        if isinstance(value, str):
            return normalize_text(value)
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
            return normalize_text(value[0])
        return ""

    def _match_tabbed_section(self, soup, scalar: str) -> str | None:
        tab_map = self._build_section_tab_map(soup)
        for title, content in tab_map.items():
            if normalize_text(content) == scalar:
                return title
        return None

    def _build_section_tab_map(self, soup) -> dict[str, str]:
        tabs = []
        for node in soup.select("[role='tab']"):
            text_node = node.select_one(".van-tab__text")
            text = normalize_text((text_node or node).get_text(" ", strip=True))
            if text:
                tabs.append(text)
        panes = soup.select(".van-tab__pane-wrapper .van-tab__pane, .van-tab__pane")
        result: dict[str, str] = {}
        for tab, pane in zip(tabs, panes):
            result[tab] = normalize_text(pane.get_text("\n", strip=True))
        return result

    def _find_text_node(self, soup, scalar: str):
        candidates = []
        for node in soup.find_all(True)[:400]:
            text = normalize_text(node.get_text(" ", strip=True))
            if not text:
                continue
            if text == scalar:
                candidates.append((0, node))
            elif scalar in text and len(text) <= len(scalar) * 2:
                candidates.append((1, node))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], len(item[1].get_text(" ", strip=True))))
        return candidates[0][1]

    def _build_css_selector(self, node, soup) -> str:
        if node.get("class"):
            classes = [class_name for class_name in node.get("class", []) if class_name]
            if classes:
                selector = f"{node.name}." + ".".join(classes[:2])
                if len(soup.select(selector)) == 1:
                    return selector
        if node.name and len(soup.select(node.name)) == 1:
            return node.name
        return ""

    def _build_label_value_selector(
        self, node, scalar: str
    ) -> FieldSelectorRule | None:
        parent = node.parent
        if parent is None:
            return None

        siblings = [child for child in parent.find_all(recursive=False) if getattr(child, "name", None)]
        if len(siblings) < 2:
            return None

        try:
            index = siblings.index(node)
        except ValueError:
            return None

        if index <= 0:
            return None

        label_node = siblings[index - 1]
        label_text = normalize_text(label_node.get_text(" ", strip=True))
        value_text = normalize_text(node.get_text(" ", strip=True))
        if not label_text or value_text != scalar:
            return None
        if len(label_text) > 40:
            return None
        if label_text == scalar:
            return None
        return FieldSelectorRule(kind="label_value", value=label_text)
