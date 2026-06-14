from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ..config import TEMPLATE_DIR
from ..models import (
    ExtractionIntent,
    ExtractionRequest,
    ExtractionResult,
    FieldEvidence,
    TemplateMatch,
)
from ..preprocessing import extract_page_description, normalize_text
from .base import BaseTemplateParser


OVERVIEW = "\u6982\u8ff0"
CAUSES = "\u75c5\u56e0"
SYMPTOMS = "\u75c7\u72b6"
DIAGNOSIS = "\u8bca\u65ad"
TREATMENT = "\u6cbb\u7597"
DAILY = "\u65e5\u5e38"
PREVENTION = "\u9884\u9632"


class DayiDiseaseTemplateParser(BaseTemplateParser):
    template_id = "dayi_disease_v1"
    site_name = "\u4e2d\u56fd\u533b\u836f\u4fe1\u606f\u67e5\u8be2\u5e73\u53f0"
    page_type = "disease_page"

    def __init__(self) -> None:
        rule_path = TEMPLATE_DIR / "dayi_disease.json"
        self.rules = json.loads(Path(rule_path).read_text(encoding="utf-8"))

    def match(
        self, request: ExtractionRequest, soup: BeautifulSoup, page_title: str
    ) -> Optional[TemplateMatch]:
        title_needles = self.rules["match"]["title_contains"]
        html_needles = self.rules["match"]["html_contains"]
        html = request.raw_html

        title_score = 1.0 if any(needle in page_title for needle in title_needles) else 0.0
        html_score = sum(1 for needle in html_needles if needle in html) / len(html_needles)
        score = round((title_score * 0.6) + (html_score * 0.4), 3)

        if score < 0.7:
            return None

        return TemplateMatch(
            template_id=self.template_id,
            site_name=self.site_name,
            match_score=score,
            page_type=self.page_type,
        )

    def extract(
        self,
        request: ExtractionRequest,
        soup: BeautifulSoup,
        intent: ExtractionIntent,
    ) -> ExtractionResult:
        tabs = [
            normalize_text(span.get_text())
            for span in soup.select(".van-tabs__nav [role='tab'] .van-tab__text")
            if normalize_text(span.get_text())
        ]
        panes = soup.select(".van-tab__pane-wrapper .van-tab__pane")

        sections: Dict[str, str] = {}
        for tab_name, pane in zip(tabs, panes):
            text = normalize_text(pane.get_text("\n", strip=True))
            if text:
                sections[tab_name] = text

        name = normalize_text(soup.find("h1").get_text()) if soup.find("h1") else ""
        description = extract_page_description(soup)

        aliases_text = self._extract_inline_item(soup, "otherName")
        aliases = self._split_cn_list(aliases_text) if aliases_text else self._extract_aliases(
            sections.get(OVERVIEW, "")
        )

        transmission = (
            self._extract_long_item(soup, "_infectivityText")
            or self._extract_value_after_label(sections.get(OVERVIEW, ""), "\u4f20\u67d3\u6027")
        ).strip("\u3002 ")

        susceptible_population = self._split_cn_list(
            self._extract_long_item(soup, "_multiplePopulation")
        )
        departments = self._split_cn_list(self._extract_inline_item(soup, "departmentList"))

        data = {
            "page_title": soup.title.get_text(strip=True) if soup.title else "",
            "page_type": self.page_type,
            "name": name,
            "summary": description,
            "aliases": aliases,
            "susceptible_population": susceptible_population,
            "transmission": transmission,
            "departments": departments,
            "causes": self._extract_bullets(sections.get(CAUSES, "")),
            "symptoms": self._extract_bullets(sections.get(SYMPTOMS, "")),
            "diagnosis": self._extract_bullets(sections.get(DIAGNOSIS, "")),
            "treatment": self._extract_bullets(sections.get(TREATMENT, "")),
            "nursing_and_precautions": self._extract_bullets(sections.get(DAILY, "")),
            "prevention": self._extract_bullets(sections.get(PREVENTION, "")),
            "sections": [
                {"title": title, "content": content[:800]}
                for title, content in sections.items()
                if title in self.rules["sections"]
            ],
        }

        evidences = [
            FieldEvidence(field_name="name", source="h1", rule_id="dayi.name.h1"),
            FieldEvidence(
                field_name="summary",
                source="meta[name=description]",
                rule_id="dayi.summary.meta_description",
            ),
        ]
        return ExtractionResult(data=data, evidences=evidences)

    def _extract_aliases(self, overview_text: str) -> List[str]:
        aliases: List[str] = []
        for marker in ("\u53c8\u79f0\u4e3a", "\u53c8\u79f0"):
            if marker in overview_text:
                after = overview_text.split(marker, 1)[1]
                candidate = after.split("\uff0c", 1)[0]
                aliases.extend(self._split_cn_list(candidate))
                break
        return aliases

    def _extract_value_after_label(self, text: str, label: str) -> str:
        if label not in text:
            return ""
        candidate = text.split(label, 1)[1]
        for stop in (
            "\u53d1\u75c5\u7387",
            "\u597d\u53d1\u4eba\u7fa4",
            "\u5c31\u8bca\u79d1\u5ba4",
            "\u5e38\u89c1\u53d1\u75c5\u90e8\u4f4d",
            "\u5e38\u89c1\u75c7\u72b6",
        ):
            if stop in candidate:
                candidate = candidate.split(stop, 1)[0]
        return normalize_text(candidate).strip("\uff1a: \u3002")

    def _extract_bullets(self, text: str) -> List[str]:
        items: List[str] = []
        for raw in text.split("\n"):
            item = normalize_text(raw).strip("\uff1a: ")
            if not item:
                continue
            if item in {
                "\u603b\u8ff0",
                "\u57fa\u672c\u75c5\u56e0",
                "\u8bca\u65ad\u539f\u5219",
                "\u6cbb\u7597\u539f\u5219",
                "\u9884\u9632\u63aa\u65bd",
            }:
                continue
            if len(item) <= 1:
                continue
            items.append(item)
        return items[:20]

    def _split_cn_list(self, text: str) -> List[str]:
        if not text:
            return []
        normalized = (
            text.replace("\u6c14\u8840\u4e0d\u8db3\u7684\u597d\u53d1\u4eba\u7fa4\u6bd4\u8f83\u5e7f\u6cdb\uff0c\u5982", "")
            .replace("\u597d\u53d1\u4eba\u7fa4\u6bd4\u8f83\u5e7f\u6cdb\uff0c\u5982", "")
            .replace("\u3001", "\uff0c")
            .replace("\u4ee5\u53ca", "\uff0c")
            .replace("\u53ca", "\uff0c")
            .replace("\u7b49", "")
        )
        return [
            item.strip("\uff0c\u3002 ")
            for item in normalized.split("\uff0c")
            if item.strip("\uff0c\u3002 ")
        ]

    def _extract_inline_item(self, soup: BeautifulSoup, item_id: str) -> str:
        node = soup.find(id=item_id)
        if not node:
            return ""
        content = node.select_one(".item-content")
        return normalize_text(content.get_text(" ", strip=True)) if content else ""

    def _extract_long_item(self, soup: BeautifulSoup, item_id: str) -> str:
        node = soup.find(id=item_id)
        if not node:
            return ""
        content = node.select_one(".item-content")
        return normalize_text(content.get_text(" ", strip=True)) if content else ""
