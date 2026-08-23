"""Jira saved-filter tools."""

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
async def filters(
    query: Annotated[
        str | None,
        "Optional saved-filter name query. Omit to list visible filters.",
    ] = None,
    start_at: Annotated[
        int,
        Field(description="Index of first filter to return", ge=0),
    ] = 0,
    max_results: Annotated[
        int,
        Field(description="Max filters to return", ge=1, le=100),
    ] = 50,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List or search saved Jira filters visible to the current user."""
    normalized_query = query.strip() if query is not None else None
    normalized_query = normalized_query or None
    await ctx.info(
        "Searching saved filters"
        + (f": {normalized_query}" if normalized_query else "")
    )

    try:
        helper = JiraHelpers(api).filters
        if normalized_query is None:
            result = helper.list(start_at=start_at, max_results=max_results)
        else:
            result = helper.search(
                normalized_query,
                start_at=start_at,
                max_results=max_results,
            )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def run_filter(
    filter_id: Annotated[str, "Saved filter ID"],
    max_results: Annotated[
        int,
        Field(description="Maximum issues to return per page", ge=1, le=50),
    ] = 20,
    fields: Annotated[
        list[str] | None,
        "Fields to include in the resolved search. Selection is whole-field; when omitted, uses summary, status, assignee, priority, issuetype, created, and updated. Assignee may contain nested identity, email, and avatar data.",
    ] = None,
    next_page_token: Annotated[
        str | None,
        "Opaque nextPageToken from the previous raw response, forwarded unchanged. Keep the filter, fields, and per-page max_results stable while paging.",
    ] = None,
    raw: Annotated[
        bool,
        "Return the complete API-shaped page as structured content and a JSON text fallback, including arbitrary requested fields and nextPageToken. This bypasses normal 30,000-character server text clipping, but MCP clients may still clip results.",
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Resolve a saved filter's JQL and return exactly one page of issues.

    The filter is resolved on every call, so it must not change while paging.
    """
    await ctx.info(f"Running saved filter {filter_id}")

    try:
        result = JiraHelpers(api).filters.run(
            filter_id,
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
