"""Read a Jira issue by key."""

from typing import Annotated

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
from jira2py import JiraAPI, JiraError
from pydantic import Field, StringConstraints

from jira2mcp.adapter import to_data_tool_result
from jira2mcp.utils import get_api

from .server import tools

IssueKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
FieldSelector = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[^\s,](?:[^\r\n,]*[^\s,])?$",
        description=(
            "One Jira field selector without surrounding whitespace or commas."
        ),
    ),
]


def _normalize_issue_key(issue_key: str) -> str:
    """Return a non-blank issue key without surrounding whitespace."""
    if not isinstance(issue_key, str):
        raise ToolError("issue_key must be a string")

    normalized = issue_key.strip()
    if not normalized:
        raise ToolError("issue_key is required and cannot be empty")
    return normalized


def _validate_fields(fields: list[str]) -> list[str]:
    """Validate one Jira selector per required fields-array item."""
    if not isinstance(fields, list) or not fields:
        raise ToolError("fields must contain at least one field selector")

    for field in fields:
        if not isinstance(field, str):
            raise ToolError("fields must contain only strings")
        if not field.strip():
            raise ToolError("field selectors must not be blank")
        if field != field.strip():
            raise ToolError("field selectors must not have surrounding whitespace")
        if "," in field:
            raise ToolError("field selectors must not contain commas")

    return fields


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def read(
    issue_key: Annotated[
        IssueKey,
        Field(description="Issue key (e.g. PROJ-123)"),
    ],
    fields: Annotated[
        list[FieldSelector],
        Field(
            min_length=1,
            description=(
                "Required Jira field selectors. Each item is one key, ID, or "
                "endpoint-supported selector."
            ),
        ),
    ],
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> ToolResult:
    """Read selected Jira issue fields as unchanged structured data."""
    normalized_issue_key = _normalize_issue_key(issue_key)
    selected_fields = _validate_fields(fields)
    await ctx.info(f"Reading issue {normalized_issue_key}")

    try:
        data = api.issues.get_issue(
            issue_id=normalized_issue_key,
            fields=selected_fields,
        )
    except JiraError as exc:
        message = f"Failed to fetch issue {normalized_issue_key}: {exc}"
        await ctx.error(message)
        raise ToolError(message) from exc

    return to_data_tool_result(data)
