"""Compatibility shim for retained shared text formatters."""

from __future__ import annotations

import json
from typing import Any

from .adf import adf_to_markdown, is_adf_value
from .models import (
    FieldMeta,
    IssueType,
    JiraComment,
    JiraUser,
    SearchResult,
    WorklogReport,
    WorklogReportRow,
    user_display,
)
from .utils import format_date


def _section(title: str) -> str:
    return f"--- [{title.upper()}] ---"


def format_comment(comment: JiraComment) -> str:
    """Format a single Jira comment."""
    author = user_display(comment.author)
    created = format_date(comment.created)
    updated = format_date(comment.updated)
    body = adf_to_markdown(comment.body)

    date_str = created
    if updated != created:
        date_str += f" (edited {updated})"

    return f"### {author} — {date_str}\n{body}"


def format_search_results(result: SearchResult, jql: str = "") -> str:
    """Format search results as a compact list."""
    if not result.issues:
        return f"No issues found for JQL: {jql}" if jql else "No issues found."

    lines = []
    for issue in result.issues:
        fields = issue.fields
        status = _named(fields.status)
        lines.append(
            f"{issue.key} — {fields.summary} [{status}] ({user_display(fields.assignee)})"
        )

    output = f"Found {len(result.issues)} issue(s)\n\n" + "\n".join(lines)
    if result.nextPageToken:
        output += "\n\n(more results available — refine JQL or increase max_results)"
    return output


def format_worklog_report(report: WorklogReport) -> str:
    """Format a worklog report as readable text."""
    selector = report.issueSelector
    account_label = report.accountId or "all users"
    lines = [
        "Worklog report",
        f"Date range: {report.startDate} to {report.endDate} (UTC; end date inclusive)",
        f"Account: {account_label}",
        f"JQL: {selector.jql}",
        (
            f"Issues scanned: {selector.issuesReturned} "
            f"(max {selector.maxIssues}{', truncated' if selector.truncated else ''})"
        ),
        f"Rows: {report.rowCount}",
        f"Total: {report.totalHours:.2f}h ({report.totalSeconds}s)",
    ]

    if selector.total is not None:
        lines.append(f"Issue search total: {selector.total}")
    if selector.nextPageToken:
        lines.append("More issues matched the JQL but were not scanned.")

    if not report.rows:
        lines.append("")
        lines.append("No matching worklogs found.")
        return "\n".join(lines)

    lines.append("")
    lines.append(_section(f"Rows ({report.rowCount})"))
    for row in report.rows:
        lines.extend(_format_worklog_row(row))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_issue_type_list(project_key: str, issue_types: list[IssueType]) -> str:
    """Format a list of issue types for display."""
    if not issue_types:
        return f"No issue types found for project {project_key}"
    lines = [f"Issue types for {project_key}:\n"]
    for issue_type in issue_types:
        subtask = " (subtask)" if issue_type.subtask else ""
        lines.append(f"  • {issue_type.name} (id: {issue_type.id}){subtask}")
    return "\n".join(lines)


def format_field_metadata(
    project_key: str,
    type_name: str,
    fields: list[FieldMeta],
) -> str:
    """Format create/edit field metadata for display."""
    if not fields:
        return f"No fields found for {project_key} / {type_name}"

    required = [field for field in fields if field.required]
    optional = [field for field in fields if not field.required]
    lines = [f"Fields for {project_key} / {type_name}:\n"]

    if required:
        lines.append("Required:")
        for field in required:
            lines.extend(_format_field(field))

    if optional:
        lines.append("")
        lines.append("Optional:")
        for field in optional:
            lines.extend(_format_field(field))

    return "\n".join(lines)


def _format_worklog_row(row: WorklogReportRow) -> list[str]:
    lines = [
        (
            f"- {row.dateTime} — {row.issueKey} — {row.displayName} "
            f"({row.accountId}) — {row.timeSpentHours:.2f}h"
        )
    ]

    detail_parts = [f"issueId: {row.issueId}"]
    if row.projectKey:
        detail_parts.append(f"project: {row.projectKey}")
    if row.issueSummary:
        detail_parts.append(f"summary: {row.issueSummary}")
    if row.worklogId:
        detail_parts.append(f"worklogId: {row.worklogId}")
    lines.append(f"  {' | '.join(detail_parts)}")

    time_parts: list[str] = []
    if row.timeSpent:
        time_parts.append(row.timeSpent)
    if row.timeSpentSeconds is not None:
        time_parts.append(f"{row.timeSpentSeconds}s")
    if time_parts:
        lines.append(f"  timeSpent: {' / '.join(time_parts)}")

    if row.started:
        lines.append(f"  started: {row.started}")
    if row.created:
        lines.append(f"  created: {row.created}")
    if row.updated:
        lines.append(f"  updated: {row.updated}")
    if row.updateAuthor:
        lines.append(f"  updateAuthor: {_format_user(row.updateAuthor)}")
    if row.visibility:
        visibility_parts = [row.visibility.type or "?"]
        if row.visibility.value:
            visibility_parts.append(row.visibility.value)
        lines.append(f"  visibility: {' / '.join(visibility_parts)}")
    if row.comment:
        lines.append("  comment:")
        lines.extend(f"    {line}" for line in _format_worklog_comment(row.comment))
    if row.properties:
        lines.append("  properties:")
        for line in json.dumps(row.properties, indent=2, default=str).splitlines():
            lines.append(f"    {line}")

    return lines


def _format_worklog_comment(comment: dict[str, Any]) -> list[str]:
    if is_adf_value(comment):
        return adf_to_markdown(comment).splitlines() or [""]
    return json.dumps(comment, indent=2, default=str).splitlines()


def _format_user(user: JiraUser) -> str:
    return f"{user.displayName} ({user.accountId})"


def _named(resource: Any) -> str:
    return resource.name if resource else "—"


def _format_field(field: FieldMeta) -> list[str]:
    lines: list[str] = []
    jira_schema = field.jira_schema
    schema_type = jira_schema.type if jira_schema else "unknown"
    custom = jira_schema.custom if jira_schema else ""
    custom_suffix = f" ({custom.split(':')[-1]})" if custom else ""
    lines.append(f'  {field.resolved_id} "{field.name}" — {schema_type}{custom_suffix}')

    if field.allowedValues:
        values = []
        for value in field.allowedValues[:30]:
            if isinstance(value, dict):
                values.append(value.get("name", value.get("value", json.dumps(value))))
            else:
                values.append(str(value))
        suffix = (
            f", ... ({len(field.allowedValues)} total)"
            if len(field.allowedValues) > 30
            else ""
        )
        lines.append(f"    Allowed values: {', '.join(values)}{suffix}")

    if field.defaultValue is not None:
        if isinstance(field.defaultValue, dict):
            default_value = field.defaultValue.get(
                "name",
                field.defaultValue.get("value", json.dumps(field.defaultValue)),
            )
        else:
            default_value = str(field.defaultValue)
        lines.append(f"    Default: {default_value}")

    return lines


__all__ = [
    "format_comment",
    "format_field_metadata",
    "format_issue_type_list",
    "format_search_results",
    "format_worklog_report",
]
