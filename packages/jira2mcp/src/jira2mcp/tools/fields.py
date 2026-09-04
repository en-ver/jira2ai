"""Get field metadata for creating or editing Jira issues."""

from typing import Annotated, Literal

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import (
    JiraHelperError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)
from pydantic import Field

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools

CanonicalFieldId = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[^\s,](?:[^\r\n,]*[^\s,])?$",
        description="One canonical Jira field ID without surrounding whitespace or commas.",
    ),
]


@tools.tool(
    tags={"metadata"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def list_fields(
    project_key: Annotated[
        str | None,
        "Optional project context filter; it does not determine issue-type or screen applicability.",
    ] = None,
    query: Annotated[
        str | None,
        "Optional case-insensitive field-name or description query.",
    ] = None,
    field_ids: Annotated[
        list[CanonicalFieldId] | None,
        Field(
            min_length=1,
            description="Canonical Jira field IDs to include. Each array item is one ID.",
        ),
    ] = None,
    field_types: Annotated[
        list[Literal["system", "custom"]] | None,
        Field(
            min_length=1,
            description="Field types to include: system and/or custom.",
        ),
    ] = None,
    start_at: Annotated[
        int,
        Field(
            description="Index of the first field to return from Jira's catalog", ge=0
        ),
    ] = 0,
    max_results: Annotated[
        int,
        Field(description="Maximum fields to return in this Jira server page", ge=1),
    ] = 20,
    raw: Annotated[
        bool,
        "Return the complete API-shaped field page, including values and Jira pagination metadata, as structured content and JSON text fallback.",
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List one searchable Jira field catalog page.

    Project context is not issue-type, create-screen, or edit-screen applicability.
    Use jira_fields for create or edit metadata.
    """
    await ctx.info("Listing Jira field catalog")

    try:
        result = JiraHelpers(api).metadata.list_fields(
            project_key,
            query=query,
            field_ids=field_ids,
            field_types=field_types,
            start_at=start_at,
            max_results=max_results,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


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
