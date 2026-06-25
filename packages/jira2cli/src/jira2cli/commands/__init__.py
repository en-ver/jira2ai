"""Command registration for jira2cli."""

from __future__ import annotations

import typer

from .attachments import register_attachment_commands
from .links import register_link_commands
from .metadata import register_metadata_commands
from .read import register_read_commands
from .search import register_search_commands
from .worklogs import register_worklog_commands
from .write import register_write_commands


def register_commands(app: typer.Typer) -> None:
    """Register jira2cli commands on the root Typer app."""
    register_read_commands(app)
    register_search_commands(app)
    register_worklog_commands(app)
    register_metadata_commands(app)
    register_write_commands(app)
    register_link_commands(app)
    register_attachment_commands(app)


__all__ = ["register_commands"]
