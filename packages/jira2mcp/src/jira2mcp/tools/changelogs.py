"""Jira changelog history tools."""

from typing import Annotated

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
from pydantic import Field, StrictInt

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
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def changelogs(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    created_at_or_after: Annotated[
        str | None,
        (
            "Inclusive ISO-8601 creation bound. The complete history is fetched "
            "before this local filter is applied."
        ),
    ] = None,
    created_before: Annotated[
        str | None,
        (
            "Exclusive ISO-8601 creation bound. The complete history is fetched "
            "before this local filter is applied."
        ),
    ] = None,
    field_ids: Annotated[
        list[CanonicalFieldId] | None,
        Field(
            min_length=1,
            description="Canonical fieldId values to retain. Each array item is one ID.",
        ),
    ] = None,
    result_start_at: Annotated[
        int,
        Field(
            ge=0,
            description=(
                "Index of the first locally filtered changelog event to return after "
                "Jira's complete history is fetched; requires result_max_results when nonzero."
            ),
        ),
    ] = 0,
    result_max_results: Annotated[
        int | None,
        Field(
            ge=1,
            description=(
                "Maximum locally filtered changelog events to return after Jira's "
                "complete history is fetched."
            ),
        ),
    ] = None,
    raw: Annotated[
        bool,
        (
            "Return the helper-owned structured changelog envelope and JSON text "
            "fallback; it may be large."
        ),
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Retrieve complete changelog history for a Jira issue.

    Optional timestamp and exact ``fieldId`` filters are applied after all Jira
    GET pages are fetched. Result pagination slices those retained events locally.
    """
    await ctx.info(f"Fetching complete changelog history for {issue_key}")

    try:
        result = JiraHelpers(api).changelogs.list(
            issue_key,
            created_at_or_after=created_at_or_after,
            created_before=created_before,
            field_ids=field_ids,
            result_start_at=result_start_at,
            result_max_results=result_max_results,
        )
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def changelogs_by_ids(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    changelog_ids: Annotated[
        list[StrictInt],
        Field(
            min_length=1,
            description="Known Jira changelog IDs; each array item is one integer ID.",
        ),
    ],
    field_ids: Annotated[
        list[CanonicalFieldId] | None,
        Field(
            min_length=1,
            description="Canonical fieldId values to retain. Each array item is one ID.",
        ),
    ] = None,
    raw: Annotated[
        bool,
        (
            "Return the helper-owned structured changelog envelope and JSON text "
            "fallback; it may be large."
        ),
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Retrieve known changelog IDs through Jira's distinct POST endpoint.

    Use ``changelogs`` to discover a complete history first. Jira controls the
    response order for this known-ID request. This operation has no result pagination.
    """
    await ctx.info(f"Fetching known changelog IDs for {issue_key}")

    try:
        result = JiraHelpers(api).changelogs.list_by_ids(
            issue_key,
            changelog_ids,
            field_ids=field_ids,
        )
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


__all__ = ["changelogs", "changelogs_by_ids"]
