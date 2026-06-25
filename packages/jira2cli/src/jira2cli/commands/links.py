"""Link-management jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def add_link_command(
    link_type: str = typer.Argument(..., help="Link type name (e.g. Blocks, Clones)"),
    outward_key: str = typer.Argument(..., help="Issue key on the outward side."),
    inward_key: str = typer.Argument(..., help="Issue key on the inward side."),
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
    """Create a link between two Jira issues."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).links.create(
            link_type,
            outward_key,
            inward_key,
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


def delete_link_command(
    link_id: str = typer.Argument(..., help="Issue link ID to delete."),
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
    """Delete a Jira issue link by ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).links.delete(link_id)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def register_link_commands(app: typer.Typer) -> None:
    """Register link-management commands."""
    app.command("add-link")(add_link_command)
    app.command("delete-link")(delete_link_command)


__all__ = [
    "add_link_command",
    "delete_link_command",
    "register_link_commands",
]
