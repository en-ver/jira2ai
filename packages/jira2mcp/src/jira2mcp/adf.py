"""Compatibility shim for moved ADF helpers."""

from jira2ai_core.adf import (
    adf_to_markdown,
    convert_adf_values,
    convert_markdown_fields,
    detect_adf_field_ids,
    is_adf_field,
    is_adf_value,
    markdown_to_adf,
)

__all__ = [
    "adf_to_markdown",
    "convert_adf_values",
    "convert_markdown_fields",
    "detect_adf_field_ids",
    "is_adf_field",
    "is_adf_value",
    "markdown_to_adf",
]
