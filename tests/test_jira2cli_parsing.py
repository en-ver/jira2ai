from __future__ import annotations

import pytest
import typer
from jira2cli.parsing import (
    parse_changelog_ids_csv,
    parse_changelog_ids_option,
    parse_field_ids_csv,
    parse_field_ids_option,
    parse_fields_csv,
    parse_fields_json,
    parse_fields_option,
    parse_json_object,
)


def test_parse_json_object_returns_none_for_missing_value() -> None:
    assert parse_json_object(None, option_name="--payload") is None


def test_parse_json_object_parses_dictionary_values() -> None:
    parsed = parse_json_object(
        '{"summary": "Test", "nested": {"count": 2}}', option_name="--payload"
    )

    assert parsed == {"summary": "Test", "nested": {"count": 2}}


def test_parse_json_object_rejects_invalid_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_json_object('{"summary": }', option_name="--payload")

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert (
        captured.err
        == "--payload: must be valid JSON (Expecting value at line 1, column 13)\n"
    )
    assert captured.out == ""


def test_parse_json_object_rejects_non_object_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_json_object("[1, 2, 3]", option_name="--payload")

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == "--payload: must be a JSON object\n"
    assert captured.out == ""


def test_parse_fields_csv_returns_none_when_omitted() -> None:
    assert parse_fields_csv(None) is None


def test_parse_fields_csv_trims_segments_and_preserves_order() -> None:
    assert parse_fields_csv(
        " summary,customfield_10001,*all,-description,summary "
    ) == [
        "summary",
        "customfield_10001",
        "*all",
        "-description",
        "summary",
    ]


@pytest.mark.parametrize(
    "value", ["", "   ", ",summary", "summary,", "summary,,status"]
)
def test_parse_fields_csv_rejects_empty_segments(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_fields_csv(value)

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == (
        "--fields: must contain comma-separated non-empty field selectors\n"
    )
    assert captured.out == ""


def test_parse_fields_option_rejects_repeated_occurrences(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_fields_option(["summary", "status"])

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == "--fields: may be provided only once\n"
    assert captured.out == ""


def test_parse_field_ids_csv_trims_segments_and_preserves_order() -> None:
    assert parse_field_ids_csv(" summary, customfield_10001 ") == [
        "summary",
        "customfield_10001",
    ]


@pytest.mark.parametrize("value", ["", "   ", ",summary", "summary,"])
def test_parse_field_ids_csv_rejects_empty_segments(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_field_ids_csv(value)

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert (
        captured.err
        == "--field-ids: must contain comma-separated non-empty field IDs\n"
    )
    assert captured.out == ""


def test_parse_field_ids_option_rejects_repeated_occurrences(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_field_ids_option(["summary", "status"])

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == "--field-ids: may be provided only once\n"
    assert captured.out == ""


def test_parse_changelog_ids_csv_trims_segments_and_preserves_order() -> None:
    assert parse_changelog_ids_csv(" 10001, 10002,10001 ") == [10001, 10002, 10001]


@pytest.mark.parametrize(
    "value", ["", "   ", ",10001", "10001,", "10001,,10002", "1.5", "[1,2]", "abc"]
)
def test_parse_changelog_ids_csv_rejects_invalid_segments(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_changelog_ids_csv(value)

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == (
        "--changelog-ids: must contain comma-separated non-empty base-10 integer IDs\n"
    )
    assert captured.out == ""


def test_parse_changelog_ids_option_rejects_repeated_occurrences(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_changelog_ids_option(["10001", "10002"])

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == "--changelog-ids: may be provided only once\n"
    assert captured.out == ""


def test_parse_fields_json_uses_expected_option_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        parse_fields_json("[1, 2, 3]")

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 2
    assert captured.err == "--fields-json: must be a JSON object\n"
    assert captured.out == ""
