from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class FieldEvidence(BaseModel):
    field_name: str
    source: str
    rule_id: Optional[str] = None


class ExtractionIntent(BaseModel):
    entity_type: Optional[str] = None
    requested_capabilities: List[str] = Field(default_factory=list)
    normalized_prompt: str


class PageClassification(BaseModel):
    site_id: str = "unknown"
    site_name: str = "unknown"
    page_type: str = "unknown"
    scenario: str = "unknown"
    confidence: float = 0.0
    signals: List[str] = Field(default_factory=list)


class PageFingerprint(BaseModel):
    dom_signature: str
    headings: List[str] = Field(default_factory=list)
    key_ids: List[str] = Field(default_factory=list)
    key_classes: List[str] = Field(default_factory=list)


class PostProcessStep(BaseModel):
    op: Literal[
        "strip",
        "strip_cn_punctuation",
        "split_cn_list",
        "unique",
        "first_non_empty_line",
    ]
    args: Dict[str, Any] = Field(default_factory=dict)


class FieldSelectorRule(BaseModel):
    kind: Literal["css", "id", "meta", "text_pattern", "section_tab", "code"]
    value: str
    attr: str = "text"
    many: bool = False


class FieldRule(BaseModel):
    field_name: str
    selectors: List[FieldSelectorRule] = Field(default_factory=list)
    postprocess: List[PostProcessStep] = Field(default_factory=list)
    fallback_value: Any = None


class ExtractionPlan(BaseModel):
    mode: Literal["declarative", "hybrid", "code"] = "declarative"
    fields: List[FieldRule] = Field(default_factory=list)
    code_entrypoint: str = ""


class TemplateFieldAnalysis(BaseModel):
    field_name: str
    value_type: Literal["string", "list", "object", "unknown"] = "unknown"
    likely_anchors: List[str] = Field(default_factory=list)
    extraction_notes: str = ""
    deterministic_feasibility: Literal["high", "medium", "low"] = "medium"


class TemplateAnalysis(BaseModel):
    summary: str
    page_cues: List[str] = Field(default_factory=list)
    field_analyses: List[TemplateFieldAnalysis] = Field(default_factory=list)
    fallback_fields: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    field: str
    issue_type: str
    message: str


class ValidationReport(BaseModel):
    passed: bool
    coverage: float
    issues: List[ValidationIssue] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    url: str = ""
    raw_html: str
    user_prompt: str


class ExtractionResult(BaseModel):
    data: Dict[str, Any]
    evidences: List[FieldEvidence] = Field(default_factory=list)


class TemplateMatch(BaseModel):
    template_id: str
    site_id: str
    site_name: str
    match_score: float
    page_type: str
    scenario: str
    version: str = "v1"


class TemplateManifest(BaseModel):
    template_id: str
    parser_key: str
    site_id: str
    site_name: str
    page_type: str
    scenario: str
    version: str = "v1"
    fingerprint: Optional[PageFingerprint] = None
    required_fields: List[str] = Field(default_factory=list)
    extraction_plan: Optional[ExtractionPlan] = None
    notes: str = ""


class TemplateCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    site_id: str
    site_name: str
    page_type: str
    scenario: str
    user_prompt: str
    source_url: str = ""
    fingerprint: PageFingerprint
    extracted_fields: List[str] = Field(default_factory=list)
    sample_data: Dict[str, Any] = Field(default_factory=dict)
    analysis: Optional[TemplateAnalysis] = None
    proposed_plan: Optional[ExtractionPlan] = None


class ExtractionResponse(BaseModel):
    request_id: str
    status: Literal["success", "failed"]
    template_id: Optional[str] = None
    page_type: Optional[str] = None
    extractor_type: Literal["deterministic", "llm", "hybrid", "none"] = "none"
    confidence: float = 0.0
    drift_detected: bool = False
    data: Dict[str, Any] = Field(default_factory=dict)
    validation_report: ValidationReport
    debug_trace: Dict[str, Any] = Field(default_factory=dict)
