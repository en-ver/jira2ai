"""Attachment jira2cli commands."""

from __future__ import annotations

from typing import cast

import typer
from jira2py.helpers import JiraHelpers
from jira2py.helpers.models import AttachmentDownloadPlan

from jira2cli import client
from jira2cli.attachment_io import (
    download_attachment_content,
    format_attachment_download_result,
)
from jira2cli.output import (
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def attachment_command(
    attachment_id: str = typer.Argument(..., help="Attachment ID (e.g. 63899)"),
    output_path: str | None = typer.Option(
        None,
        "--output-path",
        help=(
            "Path to save the attachment. Can be a directory or a full file path. "
            "Defaults to the current directory."
        ),
    ),
) -> None:
    """Download a Jira attachment by its ID."""
    try:
        api = client.get_api()
        helpers = JiraHelpers(api)
        helpers.attachments.validate_id(attachment_id)
        plan_result = helpers.attachments.plan_download(
            attachment_id,
            output_path=output_path,
        )
        plan = cast(AttachmentDownloadPlan, plan_result.data)
        download_attachment_content(plan, api=api)
        output = format_attachment_download_result(plan)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(output)


def attachment_list_command(
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
    """List attachments on a Jira issue."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).attachments.list(issue_key)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def attachment_read_command(
    attachment_id: str = typer.Argument(..., help="Attachment ID (e.g. 63899)"),
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
    """Read metadata for a Jira attachment by ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).attachments.read(attachment_id)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def attachment_download_command(
    attachment_id: str = typer.Argument(..., help="Attachment ID (e.g. 63899)"),
    output_path: str | None = typer.Option(
        None,
        "--output-path",
        help=(
            "Path to save the attachment. Can be a directory or a full file path. "
            "Defaults to the current directory."
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
    """Download a Jira attachment by ID with optional structured output."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).attachments.download(
            attachment_id,
            output_path=output_path,
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


def attachment_upload_command(
    issue_key: str = typer.Argument(..., help="Issue key (e.g. PROJ-123)"),
    path: str = typer.Argument(..., help="Local file path to upload"),
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
    """Upload a local file as a Jira issue attachment."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).attachments.upload(issue_key, path)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def attachment_delete_command(
    attachment_id: str = typer.Argument(..., help="Attachment ID (e.g. 63899)"),
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
    """Delete a Jira attachment by explicit attachment ID."""
    validate_output_options(json_output=json_output, raw_output=raw_output)

    try:
        api = client.get_api()
        result = JiraHelpers(api).attachments.delete(attachment_id)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(
        render_operation_result(
            result,
            json_output=json_output,
            raw_output=raw_output,
        )
    )


def register_attachment_commands(app: typer.Typer) -> None:
    """Register attachment commands."""
    app.command("attachment")(attachment_command)
    app.command("attachment-list")(attachment_list_command)
    app.command("attachment-read")(attachment_read_command)
    app.command("attachment-download")(attachment_download_command)
    app.command("attachment-upload")(attachment_upload_command)
    app.command("attachment-delete")(attachment_delete_command)


__all__ = [
    "attachment_command",
    "attachment_delete_command",
    "attachment_download_command",
    "attachment_list_command",
    "attachment_read_command",
    "attachment_upload_command",
    "register_attachment_commands",
]
