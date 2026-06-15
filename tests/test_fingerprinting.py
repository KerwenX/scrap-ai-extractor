from pathlib import Path

from hybrid_extractor.fingerprinting import build_fingerprint, compare_fingerprints
from hybrid_extractor.preprocessing import build_soup


def test_fingerprint_similarity_for_same_template_is_high():
    html = Path("tests/fixtures/dayi_disease_sample.html").read_text(encoding="utf-8")
    left = build_fingerprint(build_soup(html))
    right = build_fingerprint(build_soup(html))
    score = compare_fingerprints(left, right)
    assert score >= 0.95
