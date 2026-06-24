"""Output formatting functions for Jira data."""

import json
from typing import Any

from .adf import adf_to_markdown, is_adf_value
from .models import (
    FieldMeta,
    IssueType,
    JiraComment,
    JiraIssue,
    SearchResult,
    user_display,
)
from .utils import format_date, format_size

DEFAULT_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "labels",
    "components",
    "fixVersions",
    "description",
    "comment",
    "attachment",
    "subtasks",
    "issuelinks",
]

# Fields that format_issue_full knows how to render as markdown.
_FORMATTED_FIELDS = set(DEFAULT_FIELDS)


def _section(title: str) -> str:
    """Return a decorated section heading: ``--- [TITLE] ---``."""
    return f"--- [{title.upper()}] ---"


def _field_label(field_id: str, names_map: dict[str, str]) -> str:
    """Return a display label for a field: 'Display Name (field_id)' or just field_id."""
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
    """Format a full issue for display.

    Standard fields are rendered as readable markdown. Any extra fields
    (requested but not in the standard set) are appended with display names.
    ADF rich-text fields are auto-converted to markdown; others shown as JSON.
    Comments are shown as a count only — use jira_comments for details.
    """
    f = issue.fields

    lines: list[str] = [
        f"Key: {issue.key}",
        f"Summary: {f.summary}",
        f"Status: {_named(f.status)}",
        f"Type: {_named(f.issuetype)}",
        f"Priority: {_named(f.priority)}",
        f"Assignee: {user_display(f.assignee)}",
        f"Reporter: {user_display(f.reporter)}",
        f"Created: {format_date(f.created)}",
        f"Updated: {format_date(f.updated)}",
    ]

    if f.labels:
        lines.append(f"Labels: {', '.join(f.labels)}")

    if f.components:
        lines.append(f"Components: {', '.join(c.name for c in f.components)}")

    if f.fixVersions:
        lines.append(f"Fix Versions: {', '.join(v.name for v in f.fixVersions)}")

    if url:
        lines.append(f"URL: {url}")

    # Comments — count in header, direct to jira_comments tool for details
    cp = f.comment
    total = cp.total if cp else 0
    if total > 0:
        lines.append(f"Comments: {total} (use jira_comments tool to read them)")
    else:
        lines.append("Comments: none")

    # Attachments
    if f.attachment:
        lines.append("")
        lines.append(_section(f"Attachments ({len(f.attachment)})"))
        lines.append("Use jira_attachment tool with the attachment id to download")
        for att in f.attachment:
            lines.append(
                f"- {att.filename or '?'} (id: {att.id}, {att.mimeType}, {format_size(att.size)})"
            )

    # Subtasks
    if f.subtasks:
        lines.append("")
        lines.append(_section(f"Subtasks ({len(f.subtasks)})"))
        for st in f.subtasks:
            status = _named(st.fields.status)
            lines.append(f"- {st.key}: {st.fields.summary} [{status}]")

    # Issue Links
    if f.issuelinks:
        lines.append("")
        lines.append(_section(f"Issue Links ({len(f.issuelinks)})"))
        for link in f.issuelinks:
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

    # Description
    lines.append("")
    lines.append(_section("Description"))
    lines.append(adf_to_markdown(f.description))

    # Extra fields — anything requested but not in the standard formatted set
    if requested_fields:
        extra_names = [f for f in requested_fields if f not in _FORMATTED_FIELDS]
        if extra_names:
            extra_data: dict[str, Any] = {}
            raw_fields = issue.fields.model_extra or {}
            # Also check declared attributes in case of overlap
            for name in extra_names:
                if name in raw_fields:
                    extra_data[name] = raw_fields[name]
                elif hasattr(issue.fields, name):
                    val = getattr(issue.fields, name)
                    if val is not None:
                        extra_data[name] = val
            if extra_data:
                names_map = field_names or {}
                lines.append("")
                lines.append(_section("Additional Fields"))
                # Separate ADF fields (render as markdown) from plain fields (JSON)
                adf_extra: dict[str, Any] = {}
                plain_fields: dict[str, Any] = {}
                for k, v in extra_data.items():
                    if is_adf_value(v):
                        adf_extra[k] = v
                    else:
                        plain_fields[k] = v
                for k, v in adf_extra.items():
                    label = _field_label(k, names_map)
                    lines.append(_section(label))
                    lines.append(adf_to_markdown(v))
                    lines.append("")
                if plain_fields:
                    # Remap keys to include display names
                    labeled = {
                        _field_label(k, names_map): v for k, v in plain_fields.items()
                    }
                    lines.append("```json")
                    lines.append(json.dumps(labeled, indent=2, default=str))
                    lines.append("```")

    return "\n".join(lines)


def format_comment(comment: JiraComment) -> str:
    """Format a single comment.

    Args:
        comment: Parsed Jira comment.

    Returns:
        Formatted comment string.
    """
    author = user_display(comment.author)
    created = format_date(comment.created)
    updated = format_date(comment.updated)
    body = adf_to_markdown(comment.body)

    date_str = created
    if updated != created:
        date_str += f" (edited {updated})"

    return f"### {author} — {date_str}\n{body}"


def format_search_results(result: SearchResult, jql: str = "") -> str:
    """Format search results as a compact list.

    Args:
        result: Parsed search response.
        jql: The JQL query that produced these results.

    Returns:
        Formatted results string.
    """
    if not result.issues:
        return f"No issues found for JQL: {jql}" if jql else "No issues found."

    lines: list[str] = []
    for issue in result.issues:
        f = issue.fields
        status = _named(f.status)
        lines.append(
            f"{issue.key} — {f.summary} [{status}] ({user_display(f.assignee)})"
        )

    output = f"Found {len(result.issues)} issue(s)\n\n" + "\n".join(lines)

    if result.nextPageToken:
        output += "\n\n(more results available — refine JQL or increase max_results)"

    return output


def format_issue_type_list(project_key: str, issue_types: list[IssueType]) -> str:
    """Format a list of issue types for display.

    Args:
        project_key: Project key.
        issue_types: Parsed issue type list.

    Returns:
        Formatted string.
    """
    if not issue_types:
        return f"No issue types found for project {project_key}"
    lines = [f"Issue types for {project_key}:\n"]
    for it in issue_types:
        subtask = " (subtask)" if it.subtask else ""
        lines.append(f"  • {it.name} (id: {it.id}){subtask}")
    return "\n".join(lines)


def format_field_metadata(
    project_key: str, type_name: str, fields: list[FieldMeta]
) -> str:
    """Format field metadata for display.

    Args:
        project_key: Project key or issue key.
        type_name: Issue type name or "edit".
        fields: Parsed field metadata list.

    Returns:
        Formatted string with required and optional fields.
    """
    if not fields:
        return f"No fields found for {project_key} / {type_name}"

    required = [f for f in fields if f.required]
    optional = [f for f in fields if not f.required]

    lines = [f"Fields for {project_key} / {type_name}:\n"]

    if required:
        lines.append("Required:")
        for f in required:
            lines.extend(_format_field(f))

    if optional:
        lines.append("")
        lines.append("Optional:")
        for f in optional:
            lines.extend(_format_field(f))

    return "\n".join(lines)


def _named(resource: Any) -> str:
    """Extract name from an optional NamedResource."""
    return resource.name if resource else "—"


def _format_field(f: FieldMeta) -> list[str]:
    """Format a single field's metadata."""
    lines: list[str] = []
    jira_schema = f.jira_schema
    schema_type = jira_schema.type if jira_schema else "unknown"
    custom = jira_schema.custom if jira_schema else ""
    custom_suffix = f" ({custom.split(':')[-1]})" if custom else ""
    lines.append(f'  {f.resolved_id} "{f.name}" — {schema_type}{custom_suffix}')

    if f.allowedValues:
        values = []
        for v in f.allowedValues[:30]:
            if isinstance(v, dict):
                values.append(v.get("name", v.get("value", json.dumps(v))))
            else:
                values.append(str(v))
        suffix = (
            f", ... ({len(f.allowedValues)} total)" if len(f.allowedValues) > 30 else ""
        )
        lines.append(f"    Allowed values: {', '.join(values)}{suffix}")

    if f.defaultValue is not None:
        if isinstance(f.defaultValue, dict):
            dv = f.defaultValue.get(
                "name", f.defaultValue.get("value", json.dumps(f.defaultValue))
            )
        else:
            dv = str(f.defaultValue)
        lines.append(f"    Default: {dv}")

    return lines
