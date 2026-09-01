"""Transition-oriented jira2cli commands."""

from __future__ import annotations

from typing import Any

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)
from jira2cli.parsing import parse_json_object


def transitions_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    transition_id: str | None = typer.Option(
        None,
        "--transition-id",
        help="Focus expanded workflow metadata on this current transition action ID.",
    ),
    include_unavailable: bool = typer.Option(
        False,
        "--include-unavailable",
        help="Include unavailable transitions for diagnostics; do not submit them.",
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
    """Discover current expanded workflow transitions and their field metadata.

    Read the current issue first. Prefer a freshly discovered transition action ID,
    not a destination status ID; unavailable transitions are diagnostic only.
    """
    validate_output_options(json_output=json_output, raw_output=raw_output)
    transition_options: dict[str, Any] = {}
    if transition_id is not None:
        transition_options["transition_id"] = transition_id
    if include_unavailable:
        transition_options["include_unavailable_transitions"] = True

    try:
        api = client.get_api()
        result = JiraHelpers(api).metadata.transitions(issue_key, **transition_options)
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
        help="Fresh transition action ID preferred; an exact current transition name also works.",
    ),
    fields_json: str | None = typer.Option(
        None,
        "--fields-json",
        help="Native Jira transition fields as a JSON object; values are not converted.",
    ),
    update_json: str | None = typer.Option(
        None,
        "--update-json",
        help="Native Jira transition update operations as a JSON object; values are not converted.",
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
    """Apply one current transition with optional native Jira fields or update operations.

    Use fresh metadata and an action ID. Jira may accept with 204 and no issue, so
    reread afterwards; do not blindly retry a 400/409, timeout, or server error.
    """
    fields = parse_json_object(fields_json, option_name="--fields-json")
    update = parse_json_object(update_json, option_name="--update-json")
    validate_output_options(json_output=json_output, raw_output=raw_output)
    transition_options: dict[str, Any] = {}
    if fields is not None:
        transition_options["fields"] = fields
    if update is not None:
        transition_options["update"] = update

    try:
        api = client.get_api()
        result = JiraHelpers(api).issues.transition(
            issue_key,
            transition,
            **transition_options,
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


def register_transition_commands(app: typer.Typer) -> None:
    """Register transition-oriented commands."""
    app.command("transitions")(transitions_command)
    app.command("transition")(transition_command)


__all__ = [
    "register_transition_commands",
    "transition_command",
    "transitions_command",
]
