"""Add a comment to a Jira issue."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..adf import markdown_to_adf
from ..utils import get_api
from .server import tools


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def comment(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    body: Annotated[str, "Comment text in markdown"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Add a comment to a Jira issue.

    Provide the comment body in markdown — it will be converted to
    Atlassian Document Format (ADF) automatically.
    """
    adf_body = markdown_to_adf(body)

    await ctx.info(f"Adding comment to {issue_key}")
    try:
        result = api.comments.add_comment(issue_id=issue_key, body=adf_body)
    except Exception as e:
        await ctx.error(f"Failed to add comment to {issue_key}: {e}")
        raise ToolError(f"Failed to add comment to {issue_key}: {e}") from e

    if raw:
        return ToolResult(
            content=json.dumps(result, indent=2, default=str),
            structured_content=result,
        )

    return (
        f"Added comment to {issue_key}\nURL: {api.credentials.url}/browse/{issue_key}"
    )
