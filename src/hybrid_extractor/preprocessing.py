from __future__ import annotations

from bs4 import BeautifulSoup


def build_clean_soup(raw_html: str) -> BeautifulSoup:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    return soup


def clean_html(raw_html: str) -> str:
    return str(build_clean_soup(raw_html))


def build_soup(raw_html: str) -> BeautifulSoup:
    return BeautifulSoup(raw_html, "html.parser")


def extract_page_title(soup: BeautifulSoup) -> str:
    return soup.title.get_text(strip=True) if soup.title else ""


def extract_page_description(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""


def normalize_text(value: str) -> str:
    return " ".join(value.split())
