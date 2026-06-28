"""Metadata and reference jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import JiraHelperValidationError

from jira2cli import client
from jira2cli.jql import JQL_REFERENCE
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
            result = JiraHelpers(api).metadata.edit_fields(issue_key)
        else:
            if not project_key:
                raise JiraHelperValidationError(
                    "Provide either --project-key (to list issue types / create fields) "
                    "or --issue-key (to list edit fields)."
                )

            api = client.get_api()
            helpers = JiraHelpers(api)
            if issue_type:
                result = helpers.metadata.create_fields(project_key, issue_type)
            else:
                result = helpers.metadata.issue_types(project_key)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def project_command(
    project_id_or_key: str = typer.Argument(
        ...,
        help="Explicit project key or project ID.",
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
    """Get a single Jira project by explicit key or ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).metadata.project(project_id_or_key)
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
        result = JiraHelpers(api).metadata.projects(query)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def statuses_command(
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
    """List Jira statuses visible to the current user."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).metadata.statuses()
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def priorities_command(
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
    """List Jira priorities visible to the current user."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).metadata.priorities()
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
        result = JiraHelpers(api).metadata.users(query, max_results=max_results)
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
        result = JiraHelpers(api).links.types()
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
    app.command("project")(project_command)
    app.command("projects")(projects_command)
    app.command("statuses")(statuses_command)
    app.command("priorities")(priorities_command)
    app.command("users")(users_command)
    app.command("link-types")(link_types_command)
    app.command("jql-syntax")(jql_syntax_command)


__all__ = [
    "fields_command",
    "jql_syntax_command",
    "link_types_command",
    "priorities_command",
    "project_command",
    "projects_command",
    "register_metadata_commands",
    "statuses_command",
    "users_command",
]
