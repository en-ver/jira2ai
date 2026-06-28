"""Transition-oriented jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def transitions_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
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
    """List available workflow transitions for a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).metadata.transitions(issue_key)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def transition_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    transition: str = typer.Argument(
        ...,
        help="Explicit transition ID or exact transition name to apply.",
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
    """Apply a workflow transition to a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).issues.transition(issue_key, transition)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def register_transition_commands(app: typer.Typer) -> None:
    """Register transition-oriented commands."""
    app.command("transitions")(transitions_command)
    app.command("transition")(transition_command)


__all__ = [
    "register_transition_commands",
    "transition_command",
    "transitions_command",
]
