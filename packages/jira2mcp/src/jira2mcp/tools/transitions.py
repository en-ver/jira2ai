"""Jira issue transition tools."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import JiraHelperError, JiraHelperOperationError

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def transitions(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List available workflow transitions for a Jira issue."""
    await ctx.info(f"Fetching transitions for {issue_key}")

    try:
        result = JiraHelpers(api).metadata.transitions(issue_key)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def transition(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    transition: Annotated[
        str,
        "Explicit transition ID or exact transition name to apply",
    ],
    raw: Annotated[bool, "Return raw JSON from the helper result"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Apply a workflow transition to a Jira issue."""
    await ctx.info(f"Transitioning {issue_key} via {transition}")

    try:
        result = JiraHelpers(api).issues.transition(issue_key, transition)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
