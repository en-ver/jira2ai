"""Shared jira2mcp utilities."""

from __future__ import annotations

import math

from jira2py import JiraAPI

MAX_OUTPUT_CHARS = 30_000
TRUNCATION_SUFFIX = "\n\n... (output truncated)"


def get_api() -> JiraAPI:
    """Create a JiraAPI instance from environment-based credentials."""
    return JiraAPI()


def truncate(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Truncate text to max_chars with a suffix note."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + TRUNCATION_SUFFIX


def format_size(size: int | float) -> str:
    """Format a byte count into a human-readable size string."""
    if (
        not isinstance(size, (int, float))
        or math.isnan(size)
        or not math.isfinite(size)
        or size < 0
    ):
        return "unknown size"
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{int(size)} bytes"


def format_date(date_str: str | None) -> str:
    """Format an ISO-like Jira date string as YYYY-MM-DD."""
    if not date_str:
        return "—"
    return date_str[:10]


__all__ = [
    "MAX_OUTPUT_CHARS",
    "TRUNCATION_SUFFIX",
    "format_date",
    "format_size",
    "get_api",
    "truncate",
]
