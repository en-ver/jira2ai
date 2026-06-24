"""Attachment-download jira2cli commands."""

from __future__ import annotations

import typer
from jira2ai_core import client
from jira2ai_core.operations import attachments as attachment_operations

from jira2cli.output import raise_cli_exception


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
        attachment_operations.validate_attachment_id(attachment_id)
        api = client.get_api()
        plan = attachment_operations.plan_attachment_download(
            attachment_id,
            output_path=output_path,
            api=api,
        )
        attachment_operations.download_attachment_content(plan, api=api)
        output = attachment_operations.format_attachment_download_result(plan)
    except Exception as exc:
        raise_cli_exception(exc)

    typer.echo(output)


def register_attachment_commands(app: typer.Typer) -> None:
    """Register attachment-download commands."""
    app.command("attachment")(attachment_command)


__all__ = ["attachment_command", "register_attachment_commands"]
