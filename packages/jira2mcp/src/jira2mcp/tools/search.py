"""Search Jira issues using JQL."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2ai_core.client import get_api
from jira2ai_core.errors import JiraOperationError
from jira2ai_core.operations.search import search_issues
from jira2py import JiraAPI
from pydantic import Field

from jira2mcp.adapter import adapt_operation_result, to_tool_error

from .server import tools


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def search(
    jql: Annotated[str, "JQL query string (e.g. 'project = PROJ AND status = Open')"],
    max_results: Annotated[
        int, Field(description="Max issues to return", ge=1, le=50)
    ] = 20,
    fields: Annotated[
        list[str] | None,
        "Fields to include (default: summary, status, assignee, priority, issuetype, created, updated)",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Search Jira issues using JQL.

    Returns a formatted list of matching issues with key, summary, status,
    type, priority, and assignee.

    Use the jql_syntax prompt for full JQL syntax reference.

    Common JQL examples:
    - assignee = currentUser()
    - project = PROJ AND status = "In Progress"
    - sprint in openSprints()
    - text ~ "search term"
    - created >= -7d
    """
    await ctx.info(f"Searching issues: {jql}")

    try:
        result = search_issues(jql, max_results=max_results, fields=fields, api=api)
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
