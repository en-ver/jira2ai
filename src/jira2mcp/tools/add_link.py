"""Create an issue link between two Jira issues."""

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
        data = api.issue_links.create_link(
            link_type_name=link_type,
            inward_issue_key=inward_issue_key,
            outward_issue_key=outward_issue_key,
        )
    except Exception as e:
        await ctx.error(f"Failed to create link: {e}")
        raise ToolError(f"Failed to create link: {e}") from e

    if raw:
        result = {
            "status": "created",
            "link_type": link_type,
            "outward_issue": outward_issue_key,
            "inward_issue": inward_issue_key,
        }
        return ToolResult(
            content=json.dumps(result, indent=2),
            structured_content=result,
        )

    return f"Created link: {outward_issue_key} {link_type.lower()} {inward_issue_key}"
