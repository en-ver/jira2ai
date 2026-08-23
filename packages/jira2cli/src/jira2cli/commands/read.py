"""Read-oriented jira2cli commands."""

from __future__ import annotations

from typing import Literal

import typer
from jira2py import JiraError
from jira2py.helpers import JiraHelpers, format_issue

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    raise_cli_usage_error,
    render_json_payload,
    render_operation_result,
    validate_output_options,
)
from jira2cli.parsing import parse_fields_option


def read_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    fields: list[str] = typer.Option(
        ...,
        "--fields",
        help=(
            "Comma-separated Jira field keys, IDs, or selectors to retrieve. "
            "Required exactly once."
        ),
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render the unchanged Jira response as JSON.",
    ),
) -> None:
    """Read a Jira issue using an explicit field projection."""
    if not issue_key.strip():
        raise_cli_usage_error("issue_key is required and cannot be empty")
    issue_key = issue_key.strip()

    selected_fields = parse_fields_option(fields)
    if selected_fields is None:
        raise_cli_usage_error("is required", param_hint="--fields")

    try:
        api = client.get_api()
        data = api.issues.get_issue(issue_id=issue_key, fields=selected_fields)
    except JiraError as exc:
        raise_cli_exception(exc, context=f"Failed to fetch issue {issue_key}")
    except Exception as exc:
        raise_cli_exception(exc)

    if json_output:
        typer.echo(render_json_payload(data))
        return

    try:
        browse_url = f"{api.credentials.url.rstrip('/')}/browse/{data['key']}"
        text = format_issue(data, browse_url=browse_url)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(text)


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
        help="Render API-oriented output as normalized, pretty-printed JSON with sorted object keys.",
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
