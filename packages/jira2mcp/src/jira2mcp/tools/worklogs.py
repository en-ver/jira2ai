"""Build Jira worklog reports using JQL-selected issues."""

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
