"""Typer application for jira2cli."""

from __future__ import annotations

import typer

from .commands import register_commands

app = typer.Typer(
    name="jira2cli",
    help="Jira CLI powered by jira2py helpers.",
    no_args_is_help=True,
    add_completion=False,
)

register_commands(app)


@app.callback()
def callback() -> None:
    """Jira CLI powered by jira2py helpers."""


def main() -> None:
    """Run the jira2cli application."""
    app()
