"""Attachment-download jira2cli commands."""

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


def register_attachment_commands(app: typer.Typer) -> None:
    """Register attachment-download commands."""
    app.command("attachment")(attachment_command)


__all__ = ["attachment_command", "register_attachment_commands"]
