"""Create an issue link between two Jira issues."""

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
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def add_link(
    link_type: Annotated[
        str,
        "Link type name (e.g. 'Blocks', 'Clones', 'Duplicate'). "
        "Read data://jira/link-types resource for available types.",
    ],
    outward_issue_key: Annotated[
        str,
        "The issue key on the outward side (e.g. PROJ-123). "
        "For 'Blocks': this issue blocks the inward issue.",
    ],
    inward_issue_key: Annotated[
        str,
        "The issue key on the inward side (e.g. PROJ-456). "
        "For 'Blocks': this issue is blocked by the outward issue.",
    ],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Create a link between two Jira issues.

    Links are directional. The link type defines the relationship:
    outward_issue_key --[outward_description]--> inward_issue_key.
    For example, with type "Blocks": PROJ-1 blocks PROJ-2 means
    outward_issue_key=PROJ-1, inward_issue_key=PROJ-2.

    Read the data://jira/link-types resource first to see available link types
    and their inward/outward descriptions.
    """
    await ctx.info(
        f"Creating {link_type} link: {outward_issue_key} -> {inward_issue_key}"
    )

    try:
        result = JiraHelpers(api).links.create(
            link_type,
            outward_issue_key,
            inward_issue_key,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
