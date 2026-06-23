"""Delete an issue link between two Jira issues."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..utils import get_api
from .server import tools


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def delete_link(
    link_id: Annotated[
        str,
        "The ID of the issue link to delete. "
        "Visible in jira_read output as '(link id: ...)'.",
    ],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Delete an issue link by its ID.

    The link ID can be found in the jira_read tool output, shown as
    '(link id: 12345)' next to each issue link.
    """
    await ctx.info(f"Deleting issue link {link_id}")

    try:
        api.issue_links.delete_link(link_id=link_id)
    except Exception as e:
        await ctx.error(f"Failed to delete link {link_id}: {e}")
        raise ToolError(f"Failed to delete link {link_id}: {e}") from e

    if raw:
        result = {"status": "deleted", "link_id": link_id}
        return ToolResult(
            content=json.dumps(result, indent=2),
            structured_content=result,
        )

    return f"Deleted issue link {link_id}"
