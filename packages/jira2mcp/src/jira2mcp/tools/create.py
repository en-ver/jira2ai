"""Create a new Jira issue."""

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
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def create(
    project_key: Annotated[str, "Project key (e.g. PROJ)"],
    issue_type: Annotated[str, "Issue type name (e.g. Bug, Task, Story, Epic)"],
    summary: Annotated[str, "Issue title / summary"],
    description: Annotated[str | None, "Issue description in markdown"] = None,
    fields: Annotated[
        dict[str, Any] | None,
        "Additional fields as key-value pairs "
        '(e.g. {"priority": {"name": "High"}, "labels": ["backend"]}). '
        "Cannot contain 'project', 'issuetype', or 'summary' — use the explicit parameters instead",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Create a new Jira issue.

    Markdown is auto-converted to ADF for rich-text fields (description,
    environment, and custom textarea fields).

    Always use jira_fields with project_key + issue_type first to discover
    required fields on the create screen. Use jira_users to look up account
    IDs for assignee or reporter fields.
    """
    helpers = JiraHelpers(api)
    try:
        helpers.issues.validate_create(
            project_key,
            issue_type,
            summary,
            description=description,
            fields=fields,
        )
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    await ctx.info(f"Creating {issue_type} in {project_key}: {summary}")

    try:
        result = helpers.issues.create(
            project_key,
            issue_type,
            summary,
            description=description,
            fields=fields,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
