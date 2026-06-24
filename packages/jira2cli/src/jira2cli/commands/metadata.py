"""Metadata and reference jira2cli commands."""

from __future__ import annotations

import typer
from jira2ai_core import client
from jira2ai_core.errors import Jira2AIValidationError
from jira2ai_core.jql import JQL_REFERENCE
from jira2ai_core.operations import fields as field_operations
from jira2ai_core.operations import links, projects, users

from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def fields_command(
    project_key: str | None = typer.Option(
        None,
        "--project-key",
        help="Project key for issue type or create-field metadata.",
    ),
    issue_type: str | None = typer.Option(
        None,
        "--issue-type",
        help="Issue type name used with --project-key for create fields.",
    ),
    issue_key: str | None = typer.Option(
        None,
        "--issue-key",
        help="Existing issue key for edit-field metadata.",
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
    """Get field metadata for creating or editing Jira issues."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        if issue_key:
            api = client.get_api()
            result = field_operations.get_edit_fields(issue_key, api=api)
        else:
            if not project_key:
                raise Jira2AIValidationError(
                    "Provide either --project-key (to list issue types / create fields) "
                    "or --issue-key (to list edit fields)."
                )

            api = client.get_api()
            if issue_type:
                result = field_operations.get_create_fields(
                    project_key,
                    issue_type,
                    api=api,
                )
            else:
                result = field_operations.list_issue_types(project_key, api=api)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def projects_command(
    query: str | None = typer.Option(
        None,
        "--query",
        help="Filter by project key or name.",
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
    """List Jira projects accessible to the current user."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = projects.list_projects(query, api=api)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def users_command(
    query: str = typer.Argument(..., help="Search string for user name or email"),
    max_results: int = typer.Option(
        10,
        "--max-results",
        min=1,
        max=50,
        help="Maximum users to return.",
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
    """Search Jira users by name or email."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = users.search_users(query, max_results=max_results, api=api)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def link_types_command(
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
    """List available Jira issue link types."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = links.list_link_types(api=api)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def jql_syntax_command() -> None:
    """Print the shared JQL syntax reference."""
    typer.echo(JQL_REFERENCE)


def register_metadata_commands(app: typer.Typer) -> None:
    """Register metadata and reference commands."""
    app.command("fields")(fields_command)
    app.command("projects")(projects_command)
    app.command("users")(users_command)
    app.command("link-types")(link_types_command)
    app.command("jql-syntax")(jql_syntax_command)


__all__ = [
    "fields_command",
    "jql_syntax_command",
    "link_types_command",
    "projects_command",
    "register_metadata_commands",
    "users_command",
]
