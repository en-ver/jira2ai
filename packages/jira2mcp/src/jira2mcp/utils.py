"""Compatibility shim for moved shared utilities."""

from jira2ai_core.client import get_api
from jira2ai_core.utils import (
    MAX_OUTPUT_CHARS,
    TRUNCATION_SUFFIX,
    format_date,
    format_size,
    truncate,
)

__all__ = [
    "MAX_OUTPUT_CHARS",
    "TRUNCATION_SUFFIX",
    "format_date",
    "format_size",
    "get_api",
    "truncate",
]
