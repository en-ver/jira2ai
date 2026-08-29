"""Parsing helpers for jira2cli options and arguments."""

from __future__ import annotations

import json
import re
from typing import Any

from jira2cli.output import raise_cli_usage_error


def parse_json_object(
    value: str | None,
    *,
    option_name: str,
) -> dict[str, Any] | None:
    """Parse an optional JSON object string into a dictionary."""
    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise_cli_usage_error(
            f"must be valid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})",
            param_hint=option_name,
        )

    if not isinstance(parsed, dict):
        raise_cli_usage_error("must be a JSON object", param_hint=option_name)

    return parsed


def _parse_string_csv(
    value: str | None,
    *,
    option_name: str,
    item_label: str,
) -> list[str] | None:
    """Parse one comma-delimited option containing non-empty strings."""
    if value is None:
        return None

    values = [item.strip() for item in value.split(",")]
    if any(not item for item in values):
        raise_cli_usage_error(
            f"must contain comma-separated non-empty {item_label}",
            param_hint=option_name,
        )
    return values


def _parse_single_csv_option(
    values: list[str] | None,
    *,
    option_name: str,
    item_label: str,
) -> list[str] | None:
    """Parse a zero-or-one comma-delimited option occurrence."""
    if values is None:
        return None
    if len(values) != 1:
        raise_cli_usage_error("may be provided only once", param_hint=option_name)
    return _parse_string_csv(
        values[0],
        option_name=option_name,
        item_label=item_label,
    )


def parse_fields_csv(value: str | None) -> list[str] | None:
    """Parse one comma-delimited Jira field selector option."""
    return _parse_string_csv(
        value,
        option_name="--fields",
        item_label="field selectors",
    )


def parse_fields_option(values: list[str] | None) -> list[str] | None:
    """Parse a zero-or-one ``--fields`` option occurrence."""
    return _parse_single_csv_option(
        values,
        option_name="--fields",
        item_label="field selectors",
    )


def parse_field_ids_csv(value: str | None) -> list[str] | None:
    """Parse one comma-delimited canonical Jira field-ID option."""
    return _parse_string_csv(
        value,
        option_name="--field-ids",
        item_label="field IDs",
    )


def parse_field_ids_option(values: list[str] | None) -> list[str] | None:
    """Parse a zero-or-one ``--field-ids`` option occurrence."""
    return _parse_single_csv_option(
        values,
        option_name="--field-ids",
        item_label="field IDs",
    )


def parse_field_types_option(values: list[str] | None) -> list[str] | None:
    """Parse a zero-or-one ``--field-types`` option occurrence."""
    return _parse_single_csv_option(
        values,
        option_name="--field-types",
        item_label="field types",
    )


def parse_fields_json(value: str | None) -> dict[str, Any] | None:
    """Parse the ``--fields-json`` option into a dictionary."""
    return parse_json_object(value, option_name="--fields-json")


def parse_changelog_ids_csv(value: str | None) -> list[int] | None:
    """Parse one comma-delimited changelog ID selector option."""
    if value is None:
        return None

    segments = [segment.strip() for segment in value.split(",")]
    if any(not re.fullmatch(r"[+-]?[0-9]+", segment) for segment in segments):
        raise_cli_usage_error(
            "must contain comma-separated non-empty base-10 integer IDs",
            param_hint="--changelog-ids",
        )

    return [int(segment, 10) for segment in segments]


def parse_changelog_ids_option(values: list[str] | None) -> list[int] | None:
    """Parse a required exactly-once ``--changelog-ids`` option occurrence."""
    if values is None:
        return None
    if len(values) != 1:
        raise_cli_usage_error(
            "may be provided only once",
            param_hint="--changelog-ids",
        )
    return parse_changelog_ids_csv(values[0])


__all__ = [
    "parse_changelog_ids_csv",
    "parse_changelog_ids_option",
    "parse_field_ids_csv",
    "parse_field_ids_option",
    "parse_field_types_option",
    "parse_fields_csv",
    "parse_fields_json",
    "parse_fields_option",
    "parse_json_object",
]
