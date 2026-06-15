from .config import DEFAULT_MEDICAL_PROMPT, DEFAULT_OUTPUT_PROMPT
from .models import ExtractionIntent


MEDICAL_KEYWORDS = [
    "\u75be\u75c5",
    "\u75c5\u56e0",
    "\u75c7\u72b6",
    "\u8bca\u65ad",
    "\u6cbb\u7597",
    "\u9884\u9632",
    "\u6ce8\u610f\u4e8b\u9879",
]
QA_KEYWORDS = [
    "\u95ee\u7b54",
    "\u95ee\u9898",
    "\u56de\u7b54",
    "\u6458\u8981",
]


def parse_intent(user_prompt: str) -> ExtractionIntent:
    normalized = user_prompt.strip() or DEFAULT_OUTPUT_PROMPT
    entity_type = None

    if any(keyword in normalized for keyword in MEDICAL_KEYWORDS):
        entity_type = "disease_page"
    elif any(keyword in normalized for keyword in QA_KEYWORDS):
        entity_type = "qa_page"

    return ExtractionIntent(
        entity_type=entity_type,
        requested_capabilities=(
            MEDICAL_KEYWORDS
            if entity_type == "disease_page"
            else QA_KEYWORDS if entity_type == "qa_page" else []
        ),
        normalized_prompt=normalized or DEFAULT_MEDICAL_PROMPT,
    )
