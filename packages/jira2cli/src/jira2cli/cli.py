"""Typer application for jira2cli."""

from __future__ import annotations

import typer

from .client import set_credentials_file
from .commands import register_commands

app = typer.Typer(
    name="jira2cli",
    help="Jira CLI powered by jira2py helpers.",
    no_args_is_help=True,
    add_completion=False,
)

register_commands(app)


@app.callback()
def callback(
    credentials_file: str | None = typer.Option(
        None,
        "--credentials-file",
        help="Explicit path to a Jira Cloud JSON credentials file.",
    ),
) -> None:
    """Jira CLI powered by jira2py helpers."""
    set_credentials_file(credentials_file)


def main() -> None:
    """Run the jira2cli application."""
    app()
