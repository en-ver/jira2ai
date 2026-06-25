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


def search_command(
    jql: str = typer.Argument(..., help="JQL query string"),
    max_results: int = typer.Option(
        20,
        "--max-results",
        min=1,
        max=50,
        help="Maximum issues to return.",
    ),
    fields: list[str] | None = typer.Option(
        None,
        "--field",
        help="Field to include in the search response. May be repeated.",
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
    """Search Jira issues using JQL."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).search.issues(
            jql,
            max_results=max_results,
            fields=fields,
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
