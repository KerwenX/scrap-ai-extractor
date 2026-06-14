from __future__ import annotations

from bs4 import BeautifulSoup

from .models import ExtractionRequest, PageClassification
from .preprocessing import extract_page_title


class PageClassifier:
    def classify(self, request: ExtractionRequest, soup: BeautifulSoup) -> PageClassification:
        title = extract_page_title(soup)
        html = request.raw_html
        url = request.url or ""
        signals: list[str] = []

        if "dayi.org.cn" in html or "dayi.org.cn" in url or "\u4e2d\u56fd\u533b\u836f\u4fe1\u606f\u67e5\u8be2\u5e73\u53f0" in title:
            signals.append("site:dayi")
            if "van-tabs__nav" in html and "<h1" in html:
                signals.append("scenario:disease_tabs")
                return PageClassification(
                    site_id="dayi",
                    site_name="\u4e2d\u56fd\u533b\u836f\u4fe1\u606f\u67e5\u8be2\u5e73\u53f0",
                    page_type="disease_page",
                    scenario="disease_detail",
                    confidence=0.95,
                    signals=signals,
                )
            if "/qa/" in url or "\u95ee" in title:
                signals.append("scenario:qa")
                return PageClassification(
                    site_id="dayi",
                    site_name="\u4e2d\u56fd\u533b\u836f\u4fe1\u606f\u67e5\u8be2\u5e73\u53f0",
                    page_type="qa_page",
                    scenario="qa_detail",
                    confidence=0.85,
                    signals=signals,
                )

        return PageClassification(signals=signals)
