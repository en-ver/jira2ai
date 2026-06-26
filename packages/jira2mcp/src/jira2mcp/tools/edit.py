"""Update an existing Jira issue."""

from typing import Annotated, Any

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import (
    JiraHelperError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools


@tools.tool(
    tags={"write"},
    annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def edit(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    summary: Annotated[str | None, "New issue title / summary"] = None,
    description: Annotated[str | None, "New description in markdown"] = None,
    fields: Annotated[
        dict[str, Any] | None,
        "Additional fields to update as key-value pairs "
        '(e.g. {"priority": {"name": "High"}}). '
        "Cannot contain 'summary' or 'description' — use the explicit parameters instead",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Update an existing Jira issue.

    Provide at least one of summary, description, or fields.
    Markdown is auto-converted to ADF for rich-text fields (description,
    environment, and custom textarea fields).

    Use jira_fields with issue_key to discover which fields are available
    on the edit screen. Use jira_users to look up account IDs for assignee updates.
    """
    helpers = JiraHelpers(api)
    try:
        helpers.issues.validate_edit(
            issue_key,
            summary=summary,
            description=description,
            fields=fields,
        )
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    await ctx.info(f"Updating issue {issue_key}")

    try:
        result = helpers.issues.edit(
            issue_key,
            summary=summary,
            description=description,
            fields=fields,
            raw=raw,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
