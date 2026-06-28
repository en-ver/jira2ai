"""Write-oriented jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)
from jira2cli.parsing import parse_fields_json


def create_command(
    project_key: str = typer.Argument(..., help="Project key (e.g. PROJ)"),
    issue_type: str = typer.Argument(..., help="Issue type name (e.g. Bug, Task)"),
    summary: str = typer.Argument(..., help="Issue title / summary"),
    description: str | None = typer.Option(
        None,
        "--description",
        help="Issue description in markdown.",
    ),
    fields_json: str | None = typer.Option(
        None,
        "--fields-json",
        help="Additional issue fields as a JSON object.",
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
    """Create a Jira issue."""
    fields = parse_fields_json(fields_json)
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).issues.create(
            project_key,
            issue_type,
            summary,
            description=description,
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


def edit_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    summary: str | None = typer.Option(
        None,
        "--summary",
        help="New issue title / summary.",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        help="New issue description in markdown.",
    ),
    fields_json: str | None = typer.Option(
        None,
        "--fields-json",
        help="Additional fields to update as a JSON object.",
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
    """Update a Jira issue."""
    fields = parse_fields_json(fields_json)
    validate_output_options(json_output=json_output, raw_output=raw_output)
    raw = raw_output or json_output

    try:
        api = client.get_api()
        result = JiraHelpers(api).issues.edit(
            issue_key,
            summary=summary,
            description=description,
            fields=fields,
            raw=raw,
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


def comment_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    body: str = typer.Argument(..., help="Comment text in markdown"),
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
    """Add a comment to a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).comments.add(issue_key, body)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def comment_update_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    comment_id: str = typer.Argument(..., help="Comment ID"),
    body: str = typer.Argument(..., help="Replacement comment text in markdown"),
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
    """Update an existing Jira issue comment."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).comments.update(issue_key, comment_id, body)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def comment_delete_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    comment_id: str = typer.Argument(..., help="Comment ID"),
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
    """Delete a Jira issue comment by explicit issue key and comment ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).comments.delete(issue_key, comment_id)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def register_write_commands(app: typer.Typer) -> None:
    """Register write-oriented commands."""
    app.command("create")(create_command)
    app.command("edit")(edit_command)
    app.command("comment")(comment_command)
    app.command("comment-update")(comment_update_command)
    app.command("comment-delete")(comment_delete_command)


__all__ = [
    "comment_command",
    "comment_delete_command",
    "comment_update_command",
    "create_command",
    "edit_command",
    "register_write_commands",
]
