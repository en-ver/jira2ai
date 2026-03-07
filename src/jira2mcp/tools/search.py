"""Search Jira issues using JQL."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from pydantic import Field

from ..formatters import format_search_results
from ..models import SearchResult
from ..utils import get_api, truncate
from .server import tools

SEARCH_FIELDS = [
    "summary",
    "status",
    "assignee",
    "priority",
    "issuetype",
    "created",
    "updated",
]


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
    limit = min(max_results, 50)
    request_fields = fields or SEARCH_FIELDS

    try:
        data = api.search.enhanced_search(
            jql=jql,
            max_results=limit,
            fields=request_fields,
        )
    except Exception as e:
        await ctx.error(f"Failed to search issues: {e}")
        raise ToolError(f"Failed to search issues: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(data, indent=2, default=str),
            structured_content=data,
        )

    result = SearchResult.model_validate(data)
    return truncate(format_search_results(result, jql=jql))
