"""Compatibility shim for moved shared formatters."""

from __future__ import annotations

import json
from typing import Any

from jira2py.helpers.issues import DEFAULT_FIELDS

from .adf import adf_to_markdown, is_adf_value
from .models import (
    FieldMeta,
    IssueType,
    JiraComment,
    JiraIssue,
    JiraUser,
    SearchResult,
    WorklogReport,
    WorklogReportRow,
    user_display,
)
from .utils import format_date, format_size

_FORMATTED_FIELDS = set(DEFAULT_FIELDS)


def _section(title: str) -> str:
    return f"--- [{title.upper()}] ---"


def _field_label(field_id: str, names_map: dict[str, str]) -> str:
    display = names_map.get(field_id)
    if display and display != field_id:
        return f"{display} ({field_id})"
    return field_id


def format_issue_full(
    issue: JiraIssue,
    *,
    url: str = "",
    requested_fields: list[str] | None = None,
    field_names: dict[str, str] | None = None,
) -> str:
    """Format a Jira issue for readable helper output."""
    fields = issue.fields
    lines: list[str] = [
        f"Key: {issue.key}",
        f"Summary: {fields.summary}",
        f"Status: {_named(fields.status)}",
        f"Type: {_named(fields.issuetype)}",
        f"Priority: {_named(fields.priority)}",
        f"Assignee: {user_display(fields.assignee)}",
        f"Reporter: {user_display(fields.reporter)}",
        f"Created: {format_date(fields.created)}",
        f"Updated: {format_date(fields.updated)}",
    ]

    if fields.labels:
        lines.append(f"Labels: {', '.join(fields.labels)}")

    if fields.components:
        lines.append(
            f"Components: {', '.join(component.name for component in fields.components)}"
        )

    if fields.fixVersions:
        lines.append(
            f"Fix Versions: {', '.join(version.name for version in fields.fixVersions)}"
        )

    if url:
        lines.append(f"URL: {url}")

    comment_page = fields.comment
    comment_total = comment_page.total if comment_page else 0
    lines.append(f"Comments: {comment_total}" if comment_total else "Comments: none")

    if fields.attachment:
        lines.append("")
        lines.append(_section(f"Attachments ({len(fields.attachment)})"))
        for attachment in fields.attachment:
            lines.append(
                f"- {attachment.filename or '?'} (id: {attachment.id}, {attachment.mimeType}, {format_size(attachment.size)})"
            )

    if fields.subtasks:
        lines.append("")
        lines.append(_section(f"Subtasks ({len(fields.subtasks)})"))
        for subtask in fields.subtasks:
            status = _named(subtask.fields.status)
            lines.append(f"- {subtask.key}: {subtask.fields.summary} [{status}]")

    if fields.issuelinks:
        lines.append("")
        lines.append(_section(f"Issue Links ({len(fields.issuelinks)})"))
        for link in fields.issuelinks:
            if link.outwardIssue:
                target = link.outwardIssue
                direction = link.type.outward
            elif link.inwardIssue:
                target = link.inwardIssue
                direction = link.type.inward
            else:
                continue
            status = _named(target.fields.status)
            lines.append(
                f"- {direction} {target.key}: {target.fields.summary} [{status}] (link id: {link.id})"
            )

    lines.append("")
    lines.append(_section("Description"))
    lines.append(adf_to_markdown(fields.description))

    if requested_fields:
        extra_names = [
            name for name in requested_fields if name not in _FORMATTED_FIELDS
        ]
        if extra_names:
            extra_data: dict[str, Any] = {}
            raw_fields = issue.fields.model_extra or {}
            for name in extra_names:
                if name in raw_fields:
                    extra_data[name] = raw_fields[name]
                elif hasattr(issue.fields, name):
                    value = getattr(issue.fields, name)
                    if value is not None:
                        extra_data[name] = value
            if extra_data:
                names_map = field_names or {}
                lines.append("")
                lines.append(_section("Additional Fields"))
                adf_extra: dict[str, Any] = {}
                plain_fields: dict[str, Any] = {}
                for key, value in extra_data.items():
                    if is_adf_value(value):
                        adf_extra[key] = value
                    else:
                        plain_fields[key] = value
                for key, value in adf_extra.items():
                    label = _field_label(key, names_map)
                    lines.append(_section(label))
                    lines.append(adf_to_markdown(value))
                    lines.append("")
                if plain_fields:
                    labeled = {
                        _field_label(key, names_map): value
                        for key, value in plain_fields.items()
                    }
                    lines.append("```json")
                    lines.append(json.dumps(labeled, indent=2, default=str))
                    lines.append("```")

    return "\n".join(lines)


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
    "DEFAULT_FIELDS",
    "format_comment",
    "format_field_metadata",
    "format_issue_full",
    "format_issue_type_list",
    "format_search_results",
    "format_worklog_report",
]
