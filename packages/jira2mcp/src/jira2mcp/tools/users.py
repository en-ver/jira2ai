"""Search for Jira users."""

from typing import Annotated

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
        result = JiraHelpers(api).metadata.users(query, max_results=max_results)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
