"""Client helpers for jira2cli."""

from __future__ import annotations

import os

from jira2py import JiraAPI

_credentials_file: str | os.PathLike[str] | None = None


def set_credentials_file(credentials_file: str | os.PathLike[str] | None) -> None:
    """Configure an explicit Jira credentials file for the current CLI invocation."""
    global _credentials_file
    _credentials_file = credentials_file


def get_api() -> JiraAPI:
    """Create a JiraAPI instance from env vars or an explicit credentials file."""
    return JiraAPI(credentials_file=_credentials_file)


__all__ = ["get_api", "set_credentials_file"]
