from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from ..config import TEMPLATE_DIR
from ..models import (
    ExtractionIntent,
    ExtractionRequest,
    ExtractionResult,
    FieldEvidence,
    PageClassification,
    TemplateMatch,
)
from ..preprocessing import extract_page_description, normalize_text
from .base import BaseTemplateParser


class DayiQATemplateParser(BaseTemplateParser):
    template_id = "dayi_qa_v1"
    site_id = "dayi"
    site_name = "\u4e2d\u56fd\u533b\u836f\u4fe1\u606f\u67e5\u8be2\u5e73\u53f0"
    page_type = "qa_page"
    scenario = "qa_detail"

    def __init__(self) -> None:
        rule_path = TEMPLATE_DIR / "dayi_qa.json"
        self.rules = json.loads(Path(rule_path).read_text(encoding="utf-8"))

    def match(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        page_title: str,
        classification: PageClassification,
    ) -> Optional[TemplateMatch]:
        if classification.site_id != self.site_id or classification.scenario != self.scenario:
            return None

        html = request.raw_html
        title_score = 1.0 if any(
            needle in page_title for needle in self.rules["match"]["title_contains"]
        ) else 0.0
        html_score = sum(
            1 for needle in self.rules["match"]["html_contains"] if needle in html
        ) / len(self.rules["match"]["html_contains"])
        score = round((title_score * 0.4) + (html_score * 0.6), 3)
        if score < 0.7:
            return None

        return TemplateMatch(
            template_id=self.template_id,
            site_id=self.site_id,
            site_name=self.site_name,
            match_score=score,
            page_type=self.page_type,
            scenario=self.scenario,
        )

    def extract(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        intent: ExtractionIntent,
    ) -> ExtractionResult:
        title = normalize_text(soup.find("h1").get_text()) if soup.find("h1") else ""
        answer_node = soup.select_one(".qa-answer")
        summary = (
            normalize_text(answer_node.get_text("\n", strip=True)) if answer_node else ""
        )
        doctor_node = soup.select_one(".doctor-name")
        doctor_name = normalize_text(doctor_node.get_text()) if doctor_node else ""
        description = extract_page_description(soup)

        data = {
            "page_title": soup.title.get_text(strip=True) if soup.title else "",
            "page_type": self.page_type,
            "question": title,
            "summary": summary or description,
            "doctor_name": doctor_name,
            "sections": [{"title": "\u95ee\u7b54", "content": summary[:800]}] if summary else [],
        }
        evidences = [
            FieldEvidence(field_name="question", source="h1", rule_id="dayi.qa.question.h1"),
            FieldEvidence(
                field_name="summary",
                source=".qa-answer",
                rule_id="dayi.qa.answer.container",
            ),
        ]
        return ExtractionResult(data=data, evidences=evidences)
