"""Jira worklog tools."""

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
from pydantic import Field

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def worklogs(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    start_at: Annotated[
        int,
        Field(description="Index of first worklog to return", ge=0),
    ] = 0,
    max_results: Annotated[
        int,
        Field(description="Max worklogs to return", ge=1, le=100),
    ] = 50,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List worklogs on a Jira issue."""
    await ctx.info(f"Fetching worklogs for {issue_key}")

    try:
        result = JiraHelpers(api).worklogs.list(
            issue_key,
            start_at=start_at,
            max_results=max_results,
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
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def add_worklog(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    time_spent: Annotated[str, "Jira time-spent string such as '1h 30m'"],
    started: Annotated[
        str | None,
        "Optional Jira started timestamp such as 2026-06-27T09:00:00.000+0000",
    ] = None,
    comment: Annotated[str | None, "Optional worklog comment in markdown"] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Add a worklog to a Jira issue."""
    await ctx.info(f"Adding worklog to {issue_key}")

    try:
        result = JiraHelpers(api).worklogs.add(
            issue_key,
            time_spent,
            started=started,
            comment=comment,
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
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def update_worklog(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    worklog_id: Annotated[str, "Worklog ID"],
    time_spent: Annotated[
        str | None,
        "Optional Jira time-spent string such as '45m'",
    ] = None,
    started: Annotated[
        str | None,
        "Optional Jira started timestamp such as 2026-06-27T09:00:00.000+0000",
    ] = None,
    comment: Annotated[
        str | None, "Optional replacement worklog comment in markdown"
    ] = None,
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Update an existing Jira worklog."""
    await ctx.info(f"Updating worklog {worklog_id} on {issue_key}")

    try:
        result = JiraHelpers(api).worklogs.update(
            issue_key,
            worklog_id,
            time_spent=time_spent,
            started=started,
            comment=comment,
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
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def delete_worklog(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    worklog_id: Annotated[str, "Worklog ID"],
    raw: Annotated[bool, "Return raw helper result"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Delete a Jira worklog by explicit issue key and worklog ID."""
    await ctx.info(f"Deleting worklog {worklog_id} from {issue_key}")

    try:
        result = JiraHelpers(api).worklogs.delete(issue_key, worklog_id)
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def worklog_report(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format (UTC)"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format (UTC, inclusive)"],
    jql: Annotated[
        str,
        "JQL selecting the issues to scan (for a single issue, use e.g. 'issue = ABC-123')",
    ],
    account_id: Annotated[
        str | None,
        "Only include worklogs authored by this Jira accountId",
    ] = None,
    max_issues: Annotated[
        int,
        Field(description="Maximum issues to scan from the JQL result set", ge=1),
    ] = 100,
    include_details: Annotated[
        bool,
        "Include optional detail fields like updateAuthor, visibility, comment, and properties",
    ] = False,
    raw: Annotated[bool, "Return raw JSON from the shared report operation"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Build a Jira worklog report for issues selected by JQL.

    Issue selection is JQL-only. For a single issue, use a query such as
    `issue = ABC-123`.
    """
    await ctx.info(f"Building worklog report for JQL: {jql}")

    try:
        result = JiraHelpers(api).worklogs.report(
            start_date=start_date,
            end_date=end_date,
            jql=jql,
            account_id=account_id,
            max_issues=max_issues,
            include_details=include_details,
        )
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)
