from __future__ import annotations

from .models import ExtractionIntent

PROMPT_VERSION = "v1"

SYSTEM_EXTRACTION_PROMPT = (
    "You are a web extraction engine. Read the supplied HTML and return one JSON object only. "
    "Honor the user's business request, infer suitable fields from page semantics, keep field names "
    "stable and concise, prefer Chinese field names when the page and user request are mainly Chinese, "
    "and never invent unsupported facts."
)

SYSTEM_TEMPLATE_PLAN_PROMPT = (
    "Summarize a reusable extraction plan for a page template. Prefer portable selectors, explain "
    "field anchors briefly, and avoid site-specific code unless deterministic rules are insufficient."
)

SYSTEM_TEMPLATE_ANALYSIS_PROMPT = (
    "Analyze the page template before writing rules. Identify stable anchors, field shapes, repeatable "
    "sections, and which fields can or cannot be extracted deterministically."
)


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
        "5. If a section exists but content is sparse, keep the field concise rather than guessing.\n"
        "6. When the page has distinguishable metadata or sections, prefer multiple meaningful fields "
        "instead of a single catch-all field such as content or result.\n"
        "7. If the page language is mainly Chinese, field names should also prefer concise Chinese labels "
        "such as 标题、作者、摘要、医生、发布时间.\n\n"
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
    return intent.requested_capabilities
