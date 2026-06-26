"""Get field metadata for creating or editing Jira issues."""

from typing import Annotated

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
    tags={"metadata"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def fields(
    project_key: Annotated[
        str | None,
        "Project key (e.g. PROJ). Required for listing issue types or create fields",
    ] = None,
    issue_type: Annotated[
        str | None,
        "Issue type name (e.g. Bug, Task, Story). "
        "Used with project_key to get create-screen fields",
    ] = None,
    issue_key: Annotated[
        str | None,
        "Existing issue key (e.g. PROJ-123). "
        "Returns edit-screen fields. Takes precedence over project_key/issue_type",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Get field metadata for creating or editing Jira issues.

    Three modes of operation:

    1. List issue types: provide only project_key.
    2. Create fields: provide project_key + issue_type.
       Returns fields available on the Create Screen — use before jira_create.
    3. Edit fields: provide issue_key (of an existing issue).
       Returns fields available on the Edit Screen — use before jira_edit.
    """
    helpers = JiraHelpers(api)

    if issue_key:
        await ctx.info(f"Fetching edit metadata for {issue_key}")
        try:
            result = helpers.metadata.edit_fields(issue_key)
        except JiraHelperOperationError as exc:
            await ctx.error(str(exc))
            raise to_tool_error(exc) from exc
        except JiraHelperError as exc:
            raise to_tool_error(exc) from exc
        return adapt_operation_result(result, raw=raw, truncate_text=True)

    if not project_key:
        raise to_tool_error(
            JiraHelperValidationError(
                "Provide either project_key (to list issue types / create fields) "
                "or issue_key (to list edit fields)."
            )
        )

    await ctx.info(f"Fetching issue types for {project_key}")
    if not issue_type:
        try:
            result = helpers.metadata.issue_types(project_key)
        except JiraHelperOperationError as exc:
            await ctx.error(str(exc))
            raise to_tool_error(exc) from exc
        except JiraHelperError as exc:
            raise to_tool_error(exc) from exc
        return adapt_operation_result(result, raw=raw)

    await ctx.info(f"Fetching create fields for {project_key}/{issue_type}")
    try:
        result = helpers.metadata.create_fields(project_key, issue_type)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
