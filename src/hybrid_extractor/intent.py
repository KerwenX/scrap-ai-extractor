from .config import DEFAULT_MEDICAL_PROMPT, DEFAULT_OUTPUT_PROMPT
from .models import ExtractionIntent


MEDICAL_KEYWORDS = ["疾病", "病因", "症状", "诊断", "治疗", "预防", "注意事项"]


def parse_intent(user_prompt: str) -> ExtractionIntent:
    normalized = user_prompt.strip() or DEFAULT_OUTPUT_PROMPT
    entity_type = None

    if any(keyword in normalized for keyword in MEDICAL_KEYWORDS):
        entity_type = "disease_page"

    return ExtractionIntent(
        entity_type=entity_type,
        requested_capabilities=MEDICAL_KEYWORDS if entity_type else [],
        normalized_prompt=normalized or DEFAULT_MEDICAL_PROMPT,
    )
