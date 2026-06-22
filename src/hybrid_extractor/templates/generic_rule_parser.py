from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup

from ..models import (
    ExtractionIntent,
    ExtractionRequest,
    ExtractionResult,
    PageClassification,
    TemplateManifest,
    TemplateMatch,
)
from ..rule_runtime import RuleRuntime
from ..rule_runtime import PageContext
from .base import BaseTemplateParser


class GenericRuleTemplateParser(BaseTemplateParser):
    parser_key = "generic:rule"
    template_id = ""
    site_id = ""
    site_name = ""
    page_type = ""
    scenario = ""

    def __init__(self, manifest: TemplateManifest, runtime: RuleRuntime | None = None) -> None:
        self.manifest = manifest
        self.runtime = runtime or RuleRuntime()
        self.template_id = manifest.template_id
        self.site_id = manifest.site_id
        self.site_name = manifest.site_name
        self.page_type = manifest.page_type
        self.scenario = manifest.scenario
        self.parser_key = manifest.parser_key

    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
    ) -> Optional[TemplateMatch]:
        if classification.site_id != self.site_id or classification.scenario != self.scenario:
            return None
        return TemplateMatch(
            template_id=self.template_id,
            site_id=self.site_id,
            site_name=self.site_name,
            match_score=1.0,
            page_type=self.page_type,
            scenario=self.scenario,
            version=self.manifest.version,
        )

    def extract(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup | PageContext,
        intent: ExtractionIntent,
    ) -> ExtractionResult:
        if not self.manifest.extraction_plan:
            return ExtractionResult(data={})
        return self.runtime.execute(soup, self.manifest.extraction_plan)
