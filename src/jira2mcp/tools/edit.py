"""Update an existing Jira issue."""

import json
from typing import Annotated, Any

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..adf import convert_markdown_fields, detect_adf_field_ids, markdown_to_adf
from ..utils import get_api
from .server import tools


@tools.tool(
    tags={"write"},
    annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def edit(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    summary: Annotated[str | None, "New issue title / summary"] = None,
    description: Annotated[str | None, "New description in markdown"] = None,
    fields: Annotated[
        dict[str, Any] | None,
        "Additional fields to update as key-value pairs "
        '(e.g. {"priority": {"name": "High"}}). '
        "Cannot contain 'summary' or 'description' — use the explicit parameters instead",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Update an existing Jira issue.

    Provide at least one of summary, description, or fields.
    Markdown is auto-converted to ADF for rich-text fields (description,
    environment, and custom textarea fields).

    Use jira_fields with issue_key to discover which fields are available
    on the edit screen. Use jira_users to look up account IDs for assignee updates.
    """
    if not summary and not description and not fields:
        raise ToolError(
            "Nothing to update. Provide at least one of: summary, description, or fields."
        )

    if fields:
        conflicts = set(fields.keys()) & {"summary", "description"}
        if conflicts:
            raise ToolError(
                f"Use explicit parameters instead of fields for: {conflicts}"
            )

    update_fields: dict = {**(fields or {})}

    # Auto-convert markdown strings to ADF for known rich-text fields
    if update_fields:
        try:
            all_fields = api.fields.get_fields()
            adf_ids = detect_adf_field_ids(all_fields)
        except Exception:
            adf_ids = set()
        update_fields = convert_markdown_fields(update_fields, adf_ids)

    if summary:
        update_fields["summary"] = summary
    if description:
        update_fields["description"] = markdown_to_adf(description)

    await ctx.info(f"Updating issue {issue_key}")
    try:
        result = api.issues.edit_issue(
            issue_id=issue_key,
            fields=update_fields,
            return_issue=raw,
        )
    except Exception as e:
        await ctx.error(f"Failed to update issue {issue_key}: {e}")
        raise ToolError(f"Failed to update issue {issue_key}: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(result, indent=2, default=str),
            structured_content=result,
        )

    return f"Successfully updated {issue_key}\nURL: {api.credentials.url}/browse/{issue_key}"
