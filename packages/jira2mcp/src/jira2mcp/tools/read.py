"""Read a Jira issue by key."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..formatters import DEFAULT_FIELDS, format_issue_full
from ..models import JiraIssue
from ..utils import get_api, truncate
from .server import tools


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def read(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    extra_fields: Annotated[
        list[str] | None,
        "Additional fields to retrieve beyond the standard set. "
        "Standard fields are always included: summary, status, issuetype, "
        "priority, assignee, reporter, created, updated, labels, components, "
        "fixVersions, description, comment, attachment, subtasks, issuelinks. "
        "Extra fields are shown with display names; rich-text (ADF) fields "
        "are auto-converted to markdown.",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Read a Jira issue by key with full details.

    Returns formatted issue with summary, status, assignee, description,
    attachments, subtasks, and issue links. Description is converted
    from ADF to Markdown. Use jira_comments tool for comment details.
    """
    await ctx.info(f"Reading issue {issue_key}")
    request_fields = list(DEFAULT_FIELDS)
    if extra_fields:
        request_fields.extend(f for f in extra_fields if f not in request_fields)

    try:
        data = api.issues.get_issue(
            issue_id=issue_key,
            fields=",".join(request_fields),
            expand="names",
        )
    except Exception as e:
        await ctx.error(f"Failed to fetch issue {issue_key}: {e}")
        raise ToolError(f"Failed to fetch issue {issue_key}: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(data, indent=2, default=str),
            structured_content=data,
        )

    issue = JiraIssue.model_validate(data)
    names = data.get("names") or {}
    url = f"{api.credentials.url}/browse/{issue_key}"
    output = format_issue_full(
        issue,
        url=url,
        requested_fields=request_fields,
        field_names=names,
    )

    return truncate(output)
