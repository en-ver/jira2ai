"""Search Jira issues using JQL."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
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
async def search(
    jql: Annotated[str, "JQL query string (e.g. 'project = PROJ AND status = Open')"],
    max_results: Annotated[
        int, Field(description="Maximum issues to return per page", ge=1, le=50)
    ] = 20,
    fields: Annotated[
        list[str] | None,
        "Fields to include. Selection is whole-field; when omitted, uses summary, status, assignee, priority, issuetype, created, and updated. Assignee may contain nested identity, email, and avatar data.",
    ] = None,
    next_page_token: Annotated[
        str | None,
        "Opaque nextPageToken from the previous raw response, forwarded unchanged. Keep JQL, fields, and per-page max_results stable while paging.",
    ] = None,
    raw: Annotated[
        bool,
        "Return the complete API-shaped page as structured content and a JSON text fallback, including arbitrary requested fields and nextPageToken. This bypasses normal 30,000-character server text clipping, but MCP clients may still clip results.",
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Search Jira issues using JQL.

    Returns exactly one page of matching issues, formatted with key, summary,
    status, type, priority, and assignee.

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
        result = JiraHelpers(api).search.issues(
            jql,
            max_results=max_results,
            fields=fields,
            next_page_token=next_page_token,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
