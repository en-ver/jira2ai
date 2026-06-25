"""Worklog-report jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
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
    """Register worklog-report commands."""
    app.command("worklog-report")(worklog_report_command)


__all__ = ["register_worklog_commands", "worklog_report_command"]
