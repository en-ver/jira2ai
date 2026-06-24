"""Delete an issue link between two Jira issues."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2ai_core.client import get_api
from jira2ai_core.errors import JiraOperationError
from jira2ai_core.operations.links import delete_issue_link
from jira2py import JiraAPI

from jira2mcp.adapter import adapt_operation_result, to_tool_error

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
        result = delete_issue_link(link_id, api=api)
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
