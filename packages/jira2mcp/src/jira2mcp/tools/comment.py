"""Add a comment to a Jira issue."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2ai_core.client import get_api
from jira2ai_core.errors import JiraOperationError
from jira2ai_core.operations.comments import add_comment
from jira2py import JiraAPI

from jira2mcp.adapter import adapt_operation_result, to_tool_error

from .server import tools


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def comment(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    body: Annotated[str, "Comment text in markdown"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Add a comment to a Jira issue.

    Provide the comment body in markdown — it will be converted to
    Atlassian Document Format (ADF) automatically.
    """
    await ctx.info(f"Adding comment to {issue_key}")

    try:
        result = add_comment(issue_key, body, api=api)
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
