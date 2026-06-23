"""Shared utilities for the Jira MCP server."""

import math

from jira2py import JiraAPI

MAX_OUTPUT_CHARS = 30_000
TRUNCATION_SUFFIX = "\n\n... (output truncated)"


def get_api() -> JiraAPI:
    """Create a JiraAPI instance.

    Credentials are resolved by jira2py from environment variables:
    JIRA_URL, JIRA_USER, and JIRA_API_TOKEN.

    Returns:
        Configured JiraAPI instance.

    Raises:
        ValueError: If any required credential is missing.
    """
    return JiraAPI()


def truncate(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Truncate text to max_chars with a suffix note.

    Args:
        text: The text to truncate.
        max_chars: Maximum character count.

    Returns:
        Original or truncated text.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + TRUNCATION_SUFFIX


def format_size(size: int | float) -> str:
    """Format byte count to human-readable size.

    Args:
        size: Size in bytes.

    Returns:
        Formatted size string (e.g., "1.5 MB").
    """
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
    """Format ISO date string to YYYY-MM-DD.

    Args:
        date_str: ISO 8601 date string or None.

    Returns:
        Formatted date or "—".
    """
    if not date_str:
        return "—"
    return date_str[:10]
