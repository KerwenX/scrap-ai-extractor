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
