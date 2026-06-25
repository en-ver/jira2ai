"""Read-oriented jira2cli commands."""

from __future__ import annotations

from typing import Literal

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def read_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    extra_fields: list[str] | None = typer.Option(
        None,
        "--extra-field",
        help=(
            "Additional fields to retrieve beyond the standard read fields. "
            "May be repeated."
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
    """Read a Jira issue by key with full details."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).issues.read(issue_key, extra_fields=extra_fields)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def comments_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    start_at: int = typer.Option(
        0,
        "--start-at",
        min=0,
        help="Index of the first comment to return.",
    ),
    max_results: int = typer.Option(
        50,
        "--max-results",
        min=1,
        max=100,
        help="Maximum comments to return.",
    ),
    order_by: Literal["created", "-created"] = typer.Option(
        "created",
        "--order-by",
        help="Use created for oldest first or -created for newest first.",
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
    """List comments on a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).comments.list(
            issue_key,
            start_at=start_at,
            max_results=max_results,
            order_by=order_by,
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


def register_read_commands(app: typer.Typer) -> None:
    """Register read-oriented commands."""
    app.command("read")(read_command)
    app.command("comments")(comments_command)


__all__ = ["comments_command", "read_command", "register_read_commands"]
