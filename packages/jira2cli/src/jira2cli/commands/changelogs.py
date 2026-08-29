"""Changelog history jira2cli commands."""

from __future__ import annotations

import typer
from jira2py.helpers import JiraHelpers

from jira2cli import client
from jira2cli.output import (
    raise_cli_exception,
    raise_cli_usage_error,
    render_operation_result,
    validate_output_options,
)
from jira2cli.parsing import parse_changelog_ids_option, parse_field_ids_option

RAW_OUTPUT_HELP = (
    "Render API-oriented output as normalized, pretty-printed JSON with sorted "
    "object keys."
)


def changelogs_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    created_at_or_after: str | None = typer.Option(
        None,
        "--created-at-or-after",
        help=(
            "Inclusive ISO-8601 changelog creation bound, applied locally after "
            "the complete history is retrieved."
        ),
    ),
    created_before: str | None = typer.Option(
        None,
        "--created-before",
        help=(
            "Exclusive ISO-8601 changelog creation bound, applied locally after "
            "the complete history is retrieved."
        ),
    ),
    field_ids: list[str] | None = typer.Option(
        None,
        "--field-ids",
        help="Comma-separated canonical fieldId values to retain. Provide --field-ids at most once.",
    ),
    result_start_at: int = typer.Option(
        0,
        "--result-start-at",
        min=0,
        help="Index of the first locally filtered changelog event to return; requires --result-max-results when nonzero.",
    ),
    result_max_results: int | None = typer.Option(
        None,
        "--result-max-results",
        min=1,
        help="Maximum locally filtered changelog events to return after Jira's complete history is fetched.",
    ),
    raw_output: bool = typer.Option(False, "--raw", help=RAW_OUTPUT_HELP),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Retrieve the complete changelog history for one Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)
    selected_field_ids = parse_field_ids_option(field_ids)

    try:
        api = client.get_api()
        result = JiraHelpers(api).changelogs.list(
            issue_key,
            created_at_or_after=created_at_or_after,
            created_before=created_before,
            field_ids=selected_field_ids,
            result_start_at=result_start_at,
            result_max_results=result_max_results,
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


def changelogs_by_ids_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    changelog_ids: list[str] = typer.Option(
        ...,
        "--changelog-ids",
        help="Comma-separated Jira changelog IDs. Required exactly once.",
    ),
    field_ids: list[str] | None = typer.Option(
        None,
        "--field-ids",
        help="Comma-separated canonical fieldId values to retain. Provide --field-ids at most once.",
    ),
    raw_output: bool = typer.Option(False, "--raw", help=RAW_OUTPUT_HELP),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Render structured output as JSON.",
    ),
) -> None:
    """Retrieve known changelog IDs for one Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)
    parsed_changelog_ids = parse_changelog_ids_option(changelog_ids)
    selected_field_ids = parse_field_ids_option(field_ids)
    if parsed_changelog_ids is None:
        raise_cli_usage_error("is required", param_hint="--changelog-ids")

    try:
        api = client.get_api()
        result = JiraHelpers(api).changelogs.list_by_ids(
            issue_key,
            parsed_changelog_ids,
            field_ids=selected_field_ids,
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


def register_changelog_commands(app: typer.Typer) -> None:
    """Register changelog history commands."""
    app.command("changelogs")(changelogs_command)
    app.command("changelogs-by-ids")(changelogs_by_ids_command)


__all__ = [
    "changelogs_by_ids_command",
    "changelogs_command",
    "register_changelog_commands",
]
