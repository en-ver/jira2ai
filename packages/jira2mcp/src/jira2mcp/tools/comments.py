"""List comments on a Jira issue."""

from typing import Annotated, Literal

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import JiraHelperError, JiraHelperOperationError
from pydantic import Field

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def comments(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    start_at: Annotated[
        int, Field(description="Index of first comment to return", ge=0)
    ] = 0,
    max_results: Annotated[
        int, Field(description="Max comments to return", ge=1, le=100)
    ] = 50,
    order_by: Annotated[
        Literal["created", "-created"],
        "'created' for oldest first, '-created' for newest first",
    ] = "created",
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List comments on a Jira issue with pagination support.

    For most cases, the comments included in jira_read (first 50) are sufficient.
    Use this tool when you need all comments, a specific page, or reverse
    chronological order.
    """
    await ctx.info(f"Fetching comments for {issue_key}")

    try:
        result = JiraHelpers(api).comments.list(
            issue_key,
            start_at=start_at,
            max_results=max_results,
            order_by=order_by,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
