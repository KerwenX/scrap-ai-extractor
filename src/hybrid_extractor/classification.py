from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import ExtractionRequest, PageClassification
from .preprocessing import extract_page_title


class PageClassifier:
    def classify(self, request: ExtractionRequest, soup: BeautifulSoup) -> PageClassification:
        title = extract_page_title(soup)
        html = request.raw_html
        url = request.url or ""
        host = self._extract_host(url, html)
        signals: list[str] = []

        if host:
            signals.append(f"site:{host}")

        tab_count = len(soup.select("[role='tab'], .van-tab__text"))
        has_h1 = soup.find("h1") is not None
        has_answer_block = soup.select_one(".qa-answer, .answer, [itemprop='acceptedAnswer']") is not None
        has_meta_description = soup.find("meta", attrs={"name": "description"}) is not None
        heading_count = len(soup.find_all(["h1", "h2", "h3"]))

        if has_answer_block or "/qa/" in url:
            signals.append("scenario:qa_detail")
            return PageClassification(
                site_id=host or "unknown",
                site_name=host or "unknown",
                page_type="qa_page",
                scenario="qa_detail",
                confidence=0.85,
                signals=signals,
            )

        if tab_count >= 2 and has_h1:
            signals.append("scenario:detail_tabbed")
            return PageClassification(
                site_id=host or "unknown",
                site_name=host or "unknown",
                page_type="detail_page",
                scenario="detail_tabbed",
                confidence=0.8,
                signals=signals,
            )

        if has_h1 and (has_meta_description or heading_count >= 3):
            signals.append("scenario:article_detail")
            return PageClassification(
                site_id=host or "unknown",
                site_name=host or "unknown",
                page_type="article_page",
                scenario="article_detail",
                confidence=0.7,
                signals=signals,
            )

        if has_h1 or title:
            signals.append("scenario:detail_page")
            return PageClassification(
                site_id=host or "unknown",
                site_name=host or "unknown",
                page_type="detail_page",
                scenario="detail_page",
                confidence=0.55,
                signals=signals,
            )

        return PageClassification(
            site_id=host or "unknown",
            site_name=host or "unknown",
            signals=signals,
        )

    def _extract_host(self, url: str, html: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower().strip()
        if not host:
            match = re.search(r"https?://([^/\s\"'<>]+)", html, re.IGNORECASE)
            host = match.group(1).lower().strip() if match else ""
        if host.startswith("www."):
            host = host[4:]
        return host
