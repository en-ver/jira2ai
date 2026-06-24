"""Search for Jira users."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2ai_core.client import get_api
from jira2ai_core.errors import JiraOperationError
from jira2ai_core.operations.users import search_users
from jira2py import JiraAPI
from pydantic import Field

from jira2mcp.adapter import adapt_operation_result, to_tool_error

from .server import tools


@tools.tool(
    tags={"metadata"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def users(
    query: Annotated[str, "Search string to match against user name or email"],
    max_results: Annotated[
        int, Field(description="Max users to return", ge=1, le=50)
    ] = 10,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Search for Jira users by name or email.

    Returns display name and account ID which can be used in fields like
    assignee, reporter, etc. Use this to look up account IDs before
    assigning users to issues.
    """
    await ctx.info(f"Searching users: {query}")

    try:
        result = search_users(query, max_results=max_results, api=api)
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
