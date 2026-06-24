"""Compatibility shim for moved shared formatters."""

from jira2ai_core.formatters import (
    DEFAULT_FIELDS,
    format_comment,
    format_field_metadata,
    format_issue_full,
    format_issue_type_list,
    format_search_results,
)

__all__ = [
    "DEFAULT_FIELDS",
    "format_comment",
    "format_field_metadata",
    "format_issue_full",
    "format_issue_type_list",
    "format_search_results",
]
