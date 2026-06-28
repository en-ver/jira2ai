"""Worklog jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def worklogs_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    start_at: int = typer.Option(
        0,
        "--start-at",
        min=0,
        help="Index of the first worklog to return.",
    ),
    max_results: int = typer.Option(
        50,
        "--max-results",
        min=1,
        max=100,
        help="Maximum worklogs to return.",
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render the raw API payload as JSON.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """List worklogs on a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).worklogs.list(
            issue_key,
            start_at=start_at,
            max_results=max_results,
        )
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def worklog_add_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    time_spent: str = typer.Argument(
        ...,
        help="Jira time-spent string such as '1h 30m'.",
    ),
    started: str | None = typer.Option(
        None,
        "--started",
        help="Optional Jira started timestamp such as 2026-06-27T09:00:00.000+0000.",
    ),
    comment: str | None = typer.Option(
        None,
        "--comment",
        help="Optional worklog comment in markdown.",
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render the raw API payload as JSON.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Add a worklog to a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).worklogs.add(
            issue_key,
            time_spent,
            started=started,
            comment=comment,
        )
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def worklog_update_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    worklog_id: str = typer.Argument(..., help="Worklog ID"),
    time_spent: str | None = typer.Option(
        None,
        "--time-spent",
        help="Optional Jira time-spent string such as '45m'.",
    ),
    started: str | None = typer.Option(
        None,
        "--started",
        help="Optional Jira started timestamp such as 2026-06-27T09:00:00.000+0000.",
    ),
    comment: str | None = typer.Option(
        None,
        "--comment",
        help="Optional replacement worklog comment in markdown.",
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render the raw API payload as JSON.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Update an existing Jira worklog."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).worklogs.update(
            issue_key,
            worklog_id,
            time_spent=time_spent,
            started=started,
            comment=comment,
        )
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def worklog_delete_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    worklog_id: str = typer.Argument(..., help="Worklog ID"),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render the raw API payload as JSON.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Delete a Jira worklog by explicit issue key and worklog ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).worklogs.delete(issue_key, worklog_id)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def worklog_report_command(
    start_date: str = typer.Option(
        ...,
        "--start-date",
        help="Start date in YYYY-MM-DD format (UTC).",
    ),
    end_date: str = typer.Option(
        ...,
        "--end-date",
        help="End date in YYYY-MM-DD format (UTC, inclusive).",
    ),
    jql: str = typer.Option(
        ...,
        "--jql",
        help=(
            "JQL selecting the issues to scan. For a single issue, use e.g. "
            "'issue = ABC-123'."
        ),
    ),
    account_id: str | None = typer.Option(
        None,
        "--account-id",
        help="Only include worklogs authored by this Jira accountId.",
    ),
    max_issues: int = typer.Option(
        100,
        "--max-issues",
        min=1,
        help="Maximum issues to scan from the JQL result set.",
    ),
    include_details: bool = typer.Option(
        False,
        "--include-details",
        help=(
            "Include optional detail fields like updateAuthor, visibility, "
            "comment, and properties."
        ),
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render the raw API payload as JSON.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Build a Jira worklog report for JQL-selected issues."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).worklogs.report(
            start_date=start_date,
            end_date=end_date,
            jql=jql,
            account_id=account_id,
            max_issues=max_issues,
            include_details=include_details,
        )
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def register_worklog_commands(app: typer.Typer) -> None:
    """Register worklog commands."""
    app.command("worklogs")(worklogs_command)
    app.command("worklog-add")(worklog_add_command)
    app.command("worklog-update")(worklog_update_command)
    app.command("worklog-delete")(worklog_delete_command)
    app.command("worklog-report")(worklog_report_command)


__all__ = [
    "register_worklog_commands",
    "worklog_add_command",
    "worklog_delete_command",
    "worklog_report_command",
    "worklog_update_command",
    "worklogs_command",
]
