"""Search jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)
from jira2cli.parsing import parse_fields_option


def search_command(
    jql: str = typer.Argument(
        ...,
        help="JQL query for a multi-issue projected read; use key IN (...) for known issue lists.",
    ),
    max_results: int = typer.Option(
        20,
        "--max-results",
        min=1,
        max=50,
        help="Maximum issues to return per page.",
    ),
    next_page_token: str | None = typer.Option(
        None,
        "--next-page-token",
        help="Forward a non-empty opaque nextPageToken unchanged with the same query, fields, and page size.",
    ),
    fields: list[str] | None = typer.Option(
        None,
        "--fields",
        help=(
            "Comma-separated Jira field keys, IDs, or selectors. Provide --fields "
            "at most once. If omitted, fields default to summary, status, assignee, "
            "priority, issuetype, created, updated. Requested fields apply to every "
            "issue in the returned page, but may be absent or null. Projection is "
            "whole-field; envelope metadata may remain."
        ),
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render API-oriented output as normalized, pretty-printed JSON with sorted object keys.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON; use --json or --raw for arbitrary projected fields because plain output is fixed.",
    ),
) -> None:
    """Read one page of projected fields for multiple Jira issues using JQL."""
    validate_output_options(json_output=json_output, raw_output=raw_output)
    selected_fields = parse_fields_option(fields)

    try:
        api = client.get_api()
        search = JiraHelpers(api).search
        if next_page_token is None:
            result = search.issues(
                jql,
                max_results=max_results,
                fields=selected_fields,
            )
        else:
            result = search.issues(
                jql,
                max_results=max_results,
                fields=selected_fields,
                next_page_token=next_page_token,
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


def register_search_commands(app: typer.Typer) -> None:
    """Register search commands."""
    app.command("search")(search_command)


__all__ = ["register_search_commands", "search_command"]
