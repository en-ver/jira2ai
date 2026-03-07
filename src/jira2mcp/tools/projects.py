"""List Jira projects."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..models import ProjectSearchResult
from ..utils import get_api
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
        data = api.projects.search_projects(
            query=query,
            max_results=100,
            extra_params={"orderBy": "name"},
        )
    except Exception as e:
        await ctx.error(f"Failed to fetch projects: {e}")
        raise ToolError(f"Failed to fetch projects: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(data, indent=2, default=str),
            structured_content=data,
        )

    result = ProjectSearchResult.model_validate(data)

    if not result.values:
        if query:
            return f'No projects found matching "{query}"'
        return "No projects found"

    lines: list[str] = []
    header = f'Projects matching "{query}"' if query else "Projects"
    lines.append(f"{header}:\n")

    for p in result.values:
        lines.append(f"  {p.key} — {p.name}")

    if not result.isLast:
        if result.total is not None:
            more = result.total - len(result.values)
            lines.append(f"\n  ... and {more} more (refine your search)")
        else:
            lines.append("\n  ... more results available (refine your search)")

    return "\n".join(lines)
