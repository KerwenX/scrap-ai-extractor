from __future__ import annotations

import hashlib

from bs4 import BeautifulSoup

from .models import PageFingerprint
from .preprocessing import normalize_text


def build_fingerprint(soup: BeautifulSoup) -> PageFingerprint:
    nodes = []
    for tag in soup.find_all(True)[:300]:
        classes = ".".join(sorted(tag.get("class", [])[:3]))
        node = f"{tag.name}#{tag.get('id', '')}.{classes}"
        nodes.append(node)

    headings = [
        normalize_text(node.get_text())
        for node in soup.find_all(["h1", "h2", "h3"])[:20]
        if normalize_text(node.get_text())
    ]
    key_ids = sorted({node.get("id") for node in soup.find_all(True) if node.get("id")})[:20]
    classes = []
    for node in soup.find_all(True)[:300]:
        for class_name in node.get("class", [])[:3]:
            classes.append(class_name)
    key_classes = sorted(set(classes))[:30]

    dom_signature = hashlib.sha256("|".join(nodes).encode("utf-8")).hexdigest()[:16]
    return PageFingerprint(
        dom_signature=dom_signature,
        headings=headings,
        key_ids=key_ids,
        key_classes=key_classes,
    )


def compare_fingerprints(left: PageFingerprint, right: PageFingerprint) -> float:
    score = 0.0
    if left.dom_signature == right.dom_signature:
        score += 0.55

    left_headings = set(left.headings)
    right_headings = set(right.headings)
    if left_headings or right_headings:
        score += 0.25 * _jaccard(left_headings, right_headings)

    left_ids = set(left.key_ids) | set(left.key_classes)
    right_ids = set(right.key_ids) | set(right.key_classes)
    if left_ids or right_ids:
        score += 0.20 * _jaccard(left_ids, right_ids)

    return round(score, 3)


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)
