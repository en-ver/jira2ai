"""Read a Jira issue by key."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import JiraHelperError, JiraHelperOperationError

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

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

    try:
        result = JiraHelpers(api).issues.read(issue_key, extra_fields=extra_fields)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
