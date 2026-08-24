"""Saved-filter jira2cli commands."""

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


def filters_command(
    query: str | None = typer.Option(
        None,
        "--query",
        help="Optional saved-filter name query. Omit to list visible filters.",
    ),
    start_at: int = typer.Option(
        0,
        "--start-at",
        min=0,
        help="Index of the first filter to return.",
    ),
    max_results: int = typer.Option(
        50,
        "--max-results",
        min=1,
        max=100,
        help="Maximum filters to return.",
    ),
    raw_output: bool = typer.Option(
        False,
        "--raw",
        help="Render API-oriented output as normalized, pretty-printed JSON with sorted object keys.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """List or search saved Jira filters visible to the current user."""
    validate_output_options(json_output=json_output, raw_output=raw_output)
    normalized_query = query.strip() if query is not None else None
    normalized_query = normalized_query or None

    try:
        api = client.get_api()
        helper = JiraHelpers(api).filters
        if normalized_query is None:
            result = helper.list(start_at=start_at, max_results=max_results)
        else:
            result = helper.search(
                normalized_query,
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


def filter_run_command(
    filter_id: str = typer.Argument(..., help="Saved filter ID"),
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
        help="Forward a non-empty opaque nextPageToken unchanged with the same filter, fields, and page size.",
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
    """Read one page of projected fields for multiple issues from a saved filter."""
    validate_output_options(json_output=json_output, raw_output=raw_output)
    selected_fields = parse_fields_option(fields)

    try:
        api = client.get_api()
        filters = JiraHelpers(api).filters
        if next_page_token is None:
            result = filters.run(
                filter_id,
                max_results=max_results,
                fields=selected_fields,
            )
        else:
            result = filters.run(
                filter_id,
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


def register_filter_commands(app: typer.Typer) -> None:
    """Register saved-filter commands."""
    app.command("filters")(filters_command)
    app.command("filter-run")(filter_run_command)


__all__ = ["filter_run_command", "filters_command", "register_filter_commands"]
