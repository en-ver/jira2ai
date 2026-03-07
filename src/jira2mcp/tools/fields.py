"""Get field metadata for creating or editing Jira issues."""

import json
from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI

from ..formatters import format_field_metadata, format_issue_type_list
from ..models import FieldMeta, IssueType
from ..utils import get_api, truncate
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
    # Mode 3: Edit fields for an existing issue
    if issue_key:
        await ctx.info(f"Fetching edit metadata for {issue_key}")
        try:
            edit_data = api.issues.get_edit_metadata(issue_id=issue_key)
        except Exception as e:
            await ctx.error(f"Failed to fetch edit metadata for {issue_key}: {e}")
            raise ToolError(
                f"Failed to fetch edit metadata for {issue_key}: {e}"
            ) from e

        if raw:
            return ToolResult(
                content=json.dumps(edit_data, indent=2, default=str),
                structured_content=edit_data,
            )

        fields_dict = edit_data.get("fields", {})
        fields_list = [
            FieldMeta.model_validate({"fieldId": fid, **meta})
            for fid, meta in fields_dict.items()
        ]

        return truncate(format_field_metadata(issue_key, "edit", fields_list))

    # Modes 1 & 2 require project_key
    if not project_key:
        raise ToolError(
            "Provide either project_key (to list issue types / create fields) "
            "or issue_key (to list edit fields)."
        )

    # Fetch issue types for the project
    await ctx.info(f"Fetching issue types for {project_key}")
    try:
        type_data = api.issues.get_create_issue_types(project_id_or_key=project_key)
    except Exception as e:
        await ctx.error(f"Failed to fetch issue types for {project_key}: {e}")
        raise ToolError(f"Failed to fetch issue types for {project_key}: {e}") from e
    issue_types_raw = type_data.get("values", type_data.get("issueTypes", []))

    # Mode 1: List issue types
    if not issue_type:
        if raw:
            return ToolResult(
                content=json.dumps(issue_types_raw, indent=2, default=str),
                structured_content=issue_types_raw,
            )
        issue_types = [IssueType.model_validate(it) for it in issue_types_raw]
        return format_issue_type_list(project_key, issue_types)

    # Mode 2: Create fields for a specific issue type
    issue_types = [IssueType.model_validate(it) for it in issue_types_raw]
    matched = next(
        (it for it in issue_types if it.name.lower() == issue_type.lower()),
        None,
    )

    if not matched:
        available = ", ".join(it.name for it in issue_types)
        raise ToolError(
            f'Issue type "{issue_type}" not found in {project_key}. Available: {available}'
        )

    await ctx.info(f"Fetching create fields for {project_key}/{matched.name}")
    try:
        fields_data = api.issues.get_create_fields(
            project_id_or_key=project_key,
            issue_type_id=matched.id,
        )
    except Exception as e:
        await ctx.error(
            f"Failed to fetch create fields for {project_key}/{matched.name}: {e}"
        )
        raise ToolError(
            f"Failed to fetch create fields for {project_key}/{matched.name}: {e}"
        ) from e
    fields_raw = fields_data.get("values", fields_data.get("fields", []))

    if raw:
        return ToolResult(
            content=json.dumps(fields_raw, indent=2, default=str),
            structured_content=fields_raw,
        )

    fields_list = [FieldMeta.model_validate(f) for f in fields_raw]
    return truncate(format_field_metadata(project_key, matched.name, fields_list))
