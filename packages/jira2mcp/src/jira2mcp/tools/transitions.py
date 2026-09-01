"""Jira issue transition tools."""

from typing import Annotated, Any

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
    transition_id: Annotated[
        str | None,
        "Optional current transition action ID to focus expanded metadata on; discover it first.",
    ] = None,
    include_unavailable_transitions: Annotated[
        bool,
        "Include unavailable transitions for diagnostics only; never submit one as a transition.",
    ] = False,
    raw: Annotated[
        bool, "Return raw expanded Jira transition metadata as structured JSON"
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Discover current expanded workflow transitions and their Jira-native field metadata.

    Read the current issue first. Prefer a freshly discovered transition action ID
    over a name. The action ID is not a destination status ID. Inspect availability,
    screen, required fields, schema, operations, allowed/default/autocomplete values,
    and configuration before one transition request. Unavailable transitions are
    diagnostic only.
    """
    await ctx.info(f"Fetching transitions for {issue_key}")
    transition_options: dict[str, Any] = {}
    if transition_id is not None:
        transition_options["transition_id"] = transition_id
    if include_unavailable_transitions:
        transition_options["include_unavailable_transitions"] = True

    try:
        result = JiraHelpers(api).metadata.transitions(issue_key, **transition_options)
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
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def transition(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    transition: Annotated[
        str,
        "Fresh transition action ID preferred; an exact current transition name also works.",
    ],
    fields: Annotated[
        dict[str, Any] | None,
        "Optional native Jira transition fields object. Do not use a key in both fields and update; values are not converted to ADF.",
    ] = None,
    update: Annotated[
        dict[str, Any] | None,
        "Optional native Jira transition update operations object (for example comment or worklog add when metadata permits). Do not use a key in both fields and update; values are not converted to ADF.",
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the helper result"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Apply one current transition with native Jira ``fields`` or ``update`` objects.

    Submit only after fresh metadata. Jira commonly returns HTTP 204 with no issue
    object. Acceptance is not a verification: reread the issue status and changed
    fields afterwards, and inspect comments, worklogs, or changelog when relevant.
    Do not blindly retry
    a timeout, 400, 409, or 5xx response because native update operations can be
    non-idempotent.
    """
    await ctx.info(f"Transitioning {issue_key} via {transition}")
    transition_options: dict[str, Any] = {}
    if fields is not None:
        transition_options["fields"] = fields
    if update is not None:
        transition_options["update"] = update

    try:
        result = JiraHelpers(api).issues.transition(
            issue_key,
            transition,
            **transition_options,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
