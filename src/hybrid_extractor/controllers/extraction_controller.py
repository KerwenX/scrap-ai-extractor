from __future__ import annotations

from typing import Any, Dict

from ..models import ExtractionRequest
from ..services.extraction_service import ExtractionService
from ..services.template_service import TemplateService


class ExtractionController:
    def __init__(
        self,
        extraction_service: ExtractionService | None = None,
        template_service: TemplateService | None = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.extraction_service = extraction_service or ExtractionService(
            template_service=self.template_service
        )

    def extract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = ExtractionRequest.model_validate(payload)
        response = self.extraction_service.extract(request)
        return response.model_dump()

    def list_templates(self) -> Dict[str, Any]:
        manifests = [manifest.model_dump() for manifest in self.template_service.load_manifests()]
        return {"templates": manifests}

    def get_template(self, template_id: str) -> Dict[str, Any]:
        manifest = self.template_service.get_manifest(template_id)
        if manifest is None:
            raise ValueError(f"Template not found: {template_id}")
        return manifest.model_dump()

    def delete_template(self, template_id: str) -> Dict[str, Any]:
        deleted = self.template_service.delete_manifest(template_id)
        if not deleted:
            raise ValueError(f"Template not found: {template_id}")
        return {"deleted": True, "template_id": template_id}

    def delete_templates(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        template_ids = payload.get("template_ids")
        if not isinstance(template_ids, list) or not all(isinstance(item, str) for item in template_ids):
            raise ValueError("template_ids must be a list of strings.")
        deleted_count = self.template_service.delete_manifests(template_ids)
        return {
            "deleted_count": deleted_count,
            "requested_count": len(template_ids),
            "template_ids": template_ids,
        }

    def list_template_candidates(self) -> Dict[str, Any]:
        candidates = []
        for candidate in self.template_service.load_candidates():
            payload = candidate.model_dump()
            payload["promotion_check"] = self.template_service.inspect_candidate_promotability(candidate)
            candidates.append(payload)
        return {"candidates": candidates}

    def get_template_candidate(self, candidate_id: str) -> Dict[str, Any]:
        candidate = self.template_service.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"Template candidate not found: {candidate_id}")
        payload = candidate.model_dump()
        payload["promotion_check"] = self.template_service.inspect_candidate_promotability(candidate)
        return payload

    def delete_template_candidate(self, candidate_id: str) -> Dict[str, Any]:
        deleted = self.template_service.delete_candidate(candidate_id)
        if not deleted:
            raise ValueError(f"Template candidate not found: {candidate_id}")
        return {"deleted": True, "candidate_id": candidate_id}

    def promote_template_candidate(self, candidate_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = payload.get("required_fields")
        if required_fields is not None and not isinstance(required_fields, list):
            raise ValueError("required_fields must be a list when provided.")
        template_key = payload.get("template_key")
        if template_key is not None and not isinstance(template_key, str):
            raise ValueError("template_key must be a string when provided.")
        deactivate_previous_versions = bool(payload.get("deactivate_previous_versions", False))

        manifest = self.template_service.promote_candidate(
            candidate_id,
            template_key=template_key,
            required_fields=required_fields,
            deactivate_previous_versions=deactivate_previous_versions,
        )
        if manifest is None:
            candidate = self.template_service.get_candidate(candidate_id)
            if candidate is None:
                raise ValueError(f"Template candidate not found: {candidate_id}")
            check = self.template_service.inspect_candidate_promotability(candidate, required_fields)
            reason_text = "；".join(check["reasons"]) if check["reasons"] else "缺少可执行抽取规则。"
            raise ValueError(f"Template candidate not promotable: {candidate_id}. {reason_text}")
        return manifest.model_dump()

    def set_template_status(self, template_id: str, lifecycle_status: str) -> Dict[str, Any]:
        allowed = {"draft", "active", "deprecated", "archived"}
        if lifecycle_status not in allowed:
            raise ValueError(f"Invalid lifecycle_status: {lifecycle_status}")
        manifest = self.template_service.set_manifest_status(template_id, lifecycle_status)
        if manifest is None:
            raise ValueError(f"Template not found: {template_id}")
        return manifest.model_dump()

    def set_template_active(self, template_id: str, active: bool) -> Dict[str, Any]:
        manifest = self.template_service.set_manifest_active(template_id, active)
        if manifest is None:
            raise ValueError(f"Template not found: {template_id}")
        return manifest.model_dump()
