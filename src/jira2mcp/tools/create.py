"""Create a new Jira issue."""

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
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def create(
    project_key: Annotated[str, "Project key (e.g. PROJ)"],
    issue_type: Annotated[str, "Issue type name (e.g. Bug, Task, Story, Epic)"],
    summary: Annotated[str, "Issue title / summary"],
    description: Annotated[str | None, "Issue description in markdown"] = None,
    fields: Annotated[
        dict[str, Any] | None,
        "Additional fields as key-value pairs "
        '(e.g. {"priority": {"name": "High"}, "labels": ["backend"]}). '
        "Cannot contain 'project', 'issuetype', or 'summary' — use the explicit parameters instead",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Create a new Jira issue.

    Markdown is auto-converted to ADF for rich-text fields (description,
    environment, and custom textarea fields).

    Always use jira_fields with project_key + issue_type first to discover
    required fields on the create screen. Use jira_users to look up account
    IDs for assignee or reporter fields.
    """
    if fields:
        conflicts = set(fields.keys()) & {"project", "issuetype", "summary"}
        if conflicts:
            raise ToolError(
                f"Use explicit parameters instead of fields for: {conflicts}"
            )

    extra_fields: dict = {**(fields or {})}

    # Auto-convert markdown strings to ADF for known rich-text fields
    if extra_fields:
        try:
            all_fields = api.fields.get_fields()
            adf_ids = detect_adf_field_ids(all_fields)
        except Exception:
            adf_ids = set()
        extra_fields = convert_markdown_fields(extra_fields, adf_ids)

    issue_fields: dict = {
        **extra_fields,
        "project": {"key": project_key},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }

    if description:
        issue_fields["description"] = markdown_to_adf(description)

    await ctx.info(f"Creating {issue_type} in {project_key}: {summary}")
    try:
        result = api.issues.create_issue(fields=issue_fields)
    except Exception as e:
        await ctx.error(f"Failed to create issue: {e}")
        raise ToolError(f"Failed to create issue: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(result, indent=2, default=str),
            structured_content=result,
        )

    key = result.get("key", "?")
    return f"Created {key}: {summary}\nURL: {api.credentials.url}/browse/{key}"
