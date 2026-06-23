"""Field metadata operations."""

from __future__ import annotations

from jira2py import JiraAPI

from ..errors import Jira2AIValidationError, JiraOperationError
from ..formatters import format_field_metadata, format_issue_type_list
from ..models import FieldMeta, IssueType
from ..results import OperationResult


def _get_issue_types_raw(project_key: str, *, api: JiraAPI) -> list[dict]:
    try:
        type_data = api.issues.get_create_issue_types(project_id_or_key=project_key)
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to fetch issue types for {project_key}: {exc}"
        ) from exc
    return type_data.get("values", type_data.get("issueTypes", []))


def list_issue_types(project_key: str, *, api: JiraAPI) -> OperationResult:
    """List issue types available for project issue creation."""
    issue_types_raw = _get_issue_types_raw(project_key, api=api)
    issue_types = [
        IssueType.model_validate(issue_type) for issue_type in issue_types_raw
    ]
    return OperationResult.with_data(
        format_issue_type_list(project_key, issue_types),
        issue_types_raw,
    )


def get_edit_fields(issue_key: str, *, api: JiraAPI) -> OperationResult:
    """Get edit-screen field metadata for an existing Jira issue."""
    try:
        edit_data = api.issues.get_edit_metadata(issue_id=issue_key)
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to fetch edit metadata for {issue_key}: {exc}"
        ) from exc

    fields_dict = edit_data.get("fields", {})
    fields_list = [
        FieldMeta.model_validate({"fieldId": field_id, **meta})
        for field_id, meta in fields_dict.items()
    ]
    return OperationResult.with_data(
        format_field_metadata(issue_key, "edit", fields_list),
        edit_data,
    )


def get_create_fields(
    project_key: str,
    issue_type: str,
    *,
    api: JiraAPI,
) -> OperationResult:
    """Get create-screen field metadata for a project issue type."""
    issue_types_raw = _get_issue_types_raw(project_key, api=api)
    issue_types = [
        IssueType.model_validate(issue_type_data) for issue_type_data in issue_types_raw
    ]
    matched = next(
        (
            available_type
            for available_type in issue_types
            if available_type.name.lower() == issue_type.lower()
        ),
        None,
    )
    if not matched:
        available = ", ".join(available_type.name for available_type in issue_types)
        raise Jira2AIValidationError(
            f'Issue type "{issue_type}" not found in {project_key}. Available: {available}'
        )

    try:
        fields_data = api.issues.get_create_fields(
            project_id_or_key=project_key,
            issue_type_id=matched.id,
        )
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to fetch create fields for {project_key}/{matched.name}: {exc}"
        ) from exc

    fields_raw = fields_data.get("values", fields_data.get("fields", []))
    fields_list = [FieldMeta.model_validate(field) for field in fields_raw]
    return OperationResult.with_data(
        format_field_metadata(project_key, matched.name, fields_list),
        fields_raw,
    )


__all__ = ["get_create_fields", "get_edit_fields", "list_issue_types"]
