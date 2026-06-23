"""Search for Jira users."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from pydantic import Field

from ..models import JiraUser
from ..utils import get_api
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
    limit = min(max_results, 50)

    try:
        data = api.users.search_users(query=query, max_results=limit)
    except Exception as e:
        await ctx.error(f"Failed to search users: {e}")
        raise ToolError(f"Failed to search users: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(data, indent=2, default=str),
            structured_content=data,
        )

    user_list = [JiraUser.model_validate(u) for u in data]

    if not user_list:
        return f"No users found matching: {query}"

    lines = [f"Found {len(user_list)} user(s):\n"]
    for user in user_list:
        status = " (inactive)" if not user.active else ""
        lines.append(f"- {user.displayName}{status} — accountId: {user.accountId}")

    return "\n".join(lines)
