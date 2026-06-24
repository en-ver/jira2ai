"""List Jira projects."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2ai_core.client import get_api
from jira2ai_core.errors import JiraOperationError
from jira2ai_core.operations.projects import list_projects
from jira2py import JiraAPI

from jira2mcp.adapter import adapt_operation_result, to_tool_error

from .server import tools


@tools.tool(
    tags={"metadata"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def projects(
    query: Annotated[
        str | None,
        "Filter by project name or key (case insensitive). Omit to list all projects",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List Jira projects accessible to you.

    Optionally filter by name or key with a search query.
    Use this to resolve a project name to its key before calling
    jira_create or jira_fields.
    """
    await ctx.info(f"Fetching projects{f' matching: {query}' if query else ''}")

    try:
        result = list_projects(query, api=api)
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
