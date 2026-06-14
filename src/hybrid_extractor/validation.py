from __future__ import annotations

from typing import Any, Dict, Iterable

from .models import ValidationIssue, ValidationReport


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def validate_data(data: Dict[str, Any], required_fields: Iterable[str]) -> ValidationReport:
    required = list(required_fields)
    issues: list[ValidationIssue] = []
    hit_count = 0

    for field in required:
        if _has_value(data.get(field)):
            hit_count += 1
        else:
            issues.append(
                ValidationIssue(
                    field=field,
                    issue_type="missing",
                    message=f"Required field '{field}' is missing or empty.",
                )
            )

    coverage = hit_count / len(required) if required else 1.0
    passed = coverage >= 0.6 and not any(issue.field == "name" for issue in issues)
    return ValidationReport(passed=passed, coverage=coverage, issues=issues)
