from __future__ import annotations

from .models import ExtractionIntent

PROMPT_VERSION = "v1"

SYSTEM_EXTRACTION_PROMPT = (
    "You are a web extraction engine. Read the supplied HTML and return one JSON object only. "
    "Honor the user's business request, infer suitable fields from page semantics, keep field names "
    "stable and concise, and never invent unsupported facts."
)

SYSTEM_TEMPLATE_PLAN_PROMPT = (
    "Summarize a reusable extraction plan for a page template. Prefer portable selectors, explain "
    "field anchors briefly, and avoid site-specific code unless deterministic rules are insufficient."
)

SYSTEM_TEMPLATE_ANALYSIS_PROMPT = (
    "Analyze the page template before writing rules. Identify stable anchors, field shapes, repeatable "
    "sections, and which fields can or cannot be extracted deterministically."
)

DISEASE_FIELD_HINTS = [
    "name",
    "summary",
    "aliases",
    "susceptible_population",
    "transmission",
    "departments",
    "causes",
    "symptoms",
    "diagnosis",
    "treatment",
    "nursing_and_precautions",
    "prevention",
    "sections",
]

QA_FIELD_HINTS = [
    "title",
    "question",
    "answer",
    "summary",
    "sections",
]


def build_extraction_prompt(intent: ExtractionIntent) -> str:
    field_hints = _field_hints(intent)
    hint_text = ", ".join(field_hints) if field_hints else "infer fields from the user's request"

    return (
        f"[system v={PROMPT_VERSION}]\n"
        f"{SYSTEM_EXTRACTION_PROMPT}\n\n"
        "[rules]\n"
        "1. Return valid JSON only.\n"
        "2. Use the page's explicit content as evidence; omit unsupported fields.\n"
        "3. Prefer strings for scalar facts and arrays for repeated items.\n"
        "4. Normalize obvious boilerplate, but preserve domain meaning.\n"
        "5. If a section exists but content is sparse, keep the field concise rather than guessing.\n\n"
        "[field-hints]\n"
        f"Preferred fields: {hint_text}.\n\n"
        "[user-requirement]\n"
        f"{intent.normalized_prompt}\n"
    )


def build_template_plan_prompt(user_prompt: str, extracted_fields: list[str]) -> str:
    fields_text = ", ".join(extracted_fields) if extracted_fields else "none"
    return (
        f"[system v={PROMPT_VERSION}]\n"
        f"{SYSTEM_TEMPLATE_PLAN_PROMPT}\n\n"
        "[rules]\n"
        "1. Propose selectors that can migrate across machines.\n"
        "2. Prefer CSS, metadata, headings, labels, and section anchors.\n"
        "3. Separate deterministic candidates from fields that still need LLM fallback.\n\n"
        "[user-requirement]\n"
        f"{user_prompt}\n\n"
        "[observed-fields]\n"
        f"{fields_text}\n"
    )


def build_template_analysis_prompt(user_prompt: str, extracted_fields: list[str]) -> str:
    fields_text = ", ".join(extracted_fields) if extracted_fields else "none"
    return (
        f"[system v={PROMPT_VERSION}]\n"
        f"{SYSTEM_TEMPLATE_ANALYSIS_PROMPT}\n\n"
        "[rules]\n"
        "1. Analyze before proposing extraction rules.\n"
        "2. Describe stable DOM anchors, visible labels, section titles, and repeated structures.\n"
        "3. Mark fields that are poor deterministic candidates for later LLM fallback.\n\n"
        "[user-requirement]\n"
        f"{user_prompt}\n\n"
        "[observed-fields]\n"
        f"{fields_text}\n"
    )


def _field_hints(intent: ExtractionIntent) -> list[str]:
    if intent.entity_type == "disease_page":
        return DISEASE_FIELD_HINTS
    if intent.entity_type == "qa_page":
        return QA_FIELD_HINTS
    return []
