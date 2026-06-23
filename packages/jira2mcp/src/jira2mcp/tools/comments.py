"""List comments on a Jira issue."""

import json
from typing import Annotated, Literal

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from pydantic import Field

from ..formatters import format_comment
from ..models import CommentPage
from ..utils import get_api, truncate
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
    limit = min(max_results, 100)

    try:
        data = api.comments.get_comments(
            issue_id=issue_key,
            start_at=start_at,
            max_results=limit,
            order_by=order_by,
        )
    except Exception as e:
        await ctx.error(f"Failed to fetch comments for {issue_key}: {e}")
        raise ToolError(f"Failed to fetch comments for {issue_key}: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(data, indent=2, default=str),
            structured_content=data,
        )

    page = CommentPage.model_validate(data)
    actual_start = page.startAt

    if not page.comments:
        if actual_start > 0:
            return f"No comments at offset {actual_start} (total: {page.total})"
        return f"No comments on {issue_key}"

    lines: list[str] = []

    if page.total > len(page.comments) or actual_start > 0:
        end = actual_start + len(page.comments)
        lines.append(
            f"Comments on {issue_key}: showing {actual_start + 1}–{end} of {page.total}\n"
        )
    else:
        lines.append(f"Comments on {issue_key}: {page.total} total\n")

    for c in page.comments:
        lines.append(format_comment(c))
        lines.append("")

    if actual_start + len(page.comments) < page.total:
        next_start = actual_start + len(page.comments)
        lines.append(
            f"--- More comments available. Use start_at={next_start} to fetch the next page. ---"
        )

    return truncate("\n".join(lines))
