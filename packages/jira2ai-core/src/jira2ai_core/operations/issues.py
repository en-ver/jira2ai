"""Issue operations."""

from __future__ import annotations

from typing import Any

from jira2py import JiraAPI

from ..adf import convert_markdown_fields, detect_adf_field_ids, markdown_to_adf
from ..errors import Jira2AIValidationError, JiraOperationError
from ..formatters import DEFAULT_FIELDS, format_issue_full
from ..models import JiraIssue
from ..results import OperationResult

_CREATE_FIELD_CONFLICTS = frozenset({"project", "issuetype", "summary"})
_EDIT_FIELD_CONFLICTS = frozenset({"summary", "description"})


def read_issue(
    issue_key: str,
    *,
    extra_fields: list[str] | None = None,
    api: JiraAPI,
) -> OperationResult:
    """Read a Jira issue and return formatted plus raw-ready output."""
    request_fields = list(DEFAULT_FIELDS)
    if extra_fields:
        request_fields.extend(f for f in extra_fields if f not in request_fields)

    try:
        data = api.issues.get_issue(
            issue_id=issue_key,
            fields=",".join(request_fields),
            expand="names",
        )
    except Exception as exc:
        raise JiraOperationError(f"Failed to fetch issue {issue_key}: {exc}") from exc

    issue = JiraIssue.model_validate(data)
    names = data.get("names") or {}
    url = f"{api.credentials.url}/browse/{issue_key}"
    output = format_issue_full(
        issue,
        url=url,
        requested_fields=request_fields,
        field_names=names,
    )
    return OperationResult.with_data(output, data)


def create_issue(
    project_key: str,
    issue_type: str,
    summary: str,
    *,
    description: str | None = None,
    fields: dict[str, Any] | None = None,
    api: JiraAPI,
) -> OperationResult:
    """Create a Jira issue."""
    validate_create_issue_input(fields=fields)
    extra_fields = _prepare_markdown_fields(
        fields,
        reserved_fields=_CREATE_FIELD_CONFLICTS,
        api=api,
    )

    issue_fields: dict[str, Any] = {
        **extra_fields,
        "project": {"key": project_key},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }
    if description:
        issue_fields["description"] = markdown_to_adf(description)

    try:
        data = api.issues.create_issue(fields=issue_fields)
    except Exception as exc:
        raise JiraOperationError(f"Failed to create issue: {exc}") from exc

    key = data.get("key", "?")
    return OperationResult.with_data(
        f"Created {key}: {summary}\nURL: {api.credentials.url}/browse/{key}",
        data,
    )


def edit_issue(
    issue_key: str,
    *,
    summary: str | None = None,
    description: str | None = None,
    fields: dict[str, Any] | None = None,
    raw: bool = False,
    api: JiraAPI,
) -> OperationResult:
    """Update an existing Jira issue."""
    validate_edit_issue_input(
        summary=summary,
        description=description,
        fields=fields,
    )

    update_fields = _prepare_markdown_fields(
        fields,
        reserved_fields=_EDIT_FIELD_CONFLICTS,
        api=api,
    )
    if summary:
        update_fields["summary"] = summary
    if description:
        update_fields["description"] = markdown_to_adf(description)

    try:
        data = api.issues.edit_issue(
            issue_id=issue_key,
            fields=update_fields,
            return_issue=raw,
        )
    except Exception as exc:
        raise JiraOperationError(f"Failed to update issue {issue_key}: {exc}") from exc

    text = f"Successfully updated {issue_key}\nURL: {api.credentials.url}/browse/{issue_key}"
    if not raw:
        return OperationResult.text_only(text)
    if data is None:
        return OperationResult(text=text, raw_content="null")
    return OperationResult.with_data(text, data)


def validate_create_issue_input(*, fields: dict[str, Any] | None = None) -> None:
    """Validate create-issue input that should fail before adapter logging."""
    _validate_field_conflicts(fields, reserved_fields=_CREATE_FIELD_CONFLICTS)


def validate_edit_issue_input(
    *,
    summary: str | None = None,
    description: str | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    """Validate edit-issue input that should fail before adapter logging."""
    if not summary and not description and not fields:
        raise Jira2AIValidationError(
            "Nothing to update. Provide at least one of: summary, description, or fields."
        )
    _validate_field_conflicts(fields, reserved_fields=_EDIT_FIELD_CONFLICTS)


def _prepare_markdown_fields(
    fields: dict[str, Any] | None,
    *,
    reserved_fields: frozenset[str],
    api: JiraAPI,
) -> dict[str, Any]:
    extra_fields: dict[str, Any] = {**(fields or {})}
    _validate_field_conflicts(extra_fields, reserved_fields=reserved_fields)

    if not extra_fields:
        return extra_fields

    return convert_markdown_fields(extra_fields, _get_adf_field_ids(api))


def _get_adf_field_ids(api: JiraAPI) -> set[str]:
    try:
        all_fields = api.fields.get_fields()
    except Exception:
        return set()
    return detect_adf_field_ids(all_fields)


def _validate_field_conflicts(
    fields: dict[str, Any] | None,
    *,
    reserved_fields: frozenset[str],
) -> None:
    conflicts = set((fields or {}).keys()) & reserved_fields
    if conflicts:
        raise Jira2AIValidationError(
            f"Use explicit parameters instead of fields for: {conflicts}"
        )


__all__ = [
    "create_issue",
    "edit_issue",
    "read_issue",
    "validate_create_issue_input",
    "validate_edit_issue_input",
]
