"""Shared jira2mcp utilities."""

from __future__ import annotations

import os

from jira2py import JiraAPI

MAX_OUTPUT_CHARS = 30_000
TRUNCATION_SUFFIX = "\n\n... (output truncated)"

_credentials_file: str | os.PathLike[str] | None = None


def set_credentials_file(credentials_file: str | os.PathLike[str] | None) -> None:
    """Configure an explicit Jira credentials file for server-launched tools."""
    global _credentials_file
    _credentials_file = credentials_file


def get_api() -> JiraAPI:
    """Create a JiraAPI instance from env vars or an explicit credentials file."""
    return JiraAPI(credentials_file=_credentials_file)


def truncate(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Truncate text to max_chars with a suffix note."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + TRUNCATION_SUFFIX


def format_date(date_str: str | None) -> str:
    """Format an ISO-like Jira date string as YYYY-MM-DD."""
    if not date_str:
        return "—"
    return date_str[:10]


__all__ = [
    "MAX_OUTPUT_CHARS",
    "TRUNCATION_SUFFIX",
    "format_date",
    "get_api",
    "set_credentials_file",
    "truncate",
]
