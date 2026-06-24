from __future__ import annotations

import json

import pytest
import typer
from jira2ai_core.errors import Jira2AIError, Jira2AIValidationError, JiraOperationError
from jira2ai_core.results import OperationResult
from jira2cli.output import (
    error_exit_code,
    format_cli_error,
    raise_cli_error,
    raise_cli_exception,
    render_operation_result,
    validate_output_options,
)


def test_render_operation_result_returns_text_by_default() -> None:
    result = OperationResult.text_only("formatted output")

    rendered = render_operation_result(result)

    assert rendered == "formatted output"


def test_render_operation_result_json_prefers_structured_data() -> None:
    payload = {"z": 1, "a": ["x", "y"]}
    result = OperationResult.with_data(
        "formatted output",
        payload,
        raw_content='{"ignored":true}',
    )

    rendered = render_operation_result(result, json_output=True)

    assert rendered == json.dumps(payload, indent=2, sort_keys=True, default=str)


def test_render_operation_result_raw_output_normalizes_raw_content() -> None:
    result = OperationResult(
        text="formatted output",
        raw_content='{"z": 1, "a": 2}',
    )

    rendered = render_operation_result(result, raw_output=True)

    assert rendered == '{\n  "a": 2,\n  "z": 1\n}'


def test_render_operation_result_json_falls_back_to_text() -> None:
    result = OperationResult.text_only("formatted output")

    rendered = render_operation_result(result, json_output=True)

    assert rendered == json.dumps(
        "formatted output", indent=2, sort_keys=True, default=str
    )


def test_format_cli_error_includes_sorted_details() -> None:
    error = Jira2AIError("operation failed", details={"z": 1, "a": "first"})

    formatted = format_cli_error(error)

    assert formatted == ('operation failed\nDetails:\n{\n  "a": "first",\n  "z": 1\n}')


def test_error_exit_code_uses_usage_error_for_validation_errors() -> None:
    assert error_exit_code(Jira2AIValidationError("bad input")) == 2
    assert error_exit_code(JiraOperationError("request failed")) == 1


def test_raise_cli_error_writes_to_stderr_and_exits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        raise_cli_error(JiraOperationError("request failed"))

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 1
    assert captured.err == "request failed\n"
    assert captured.out == ""


def test_raise_cli_exception_handles_non_core_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        raise_cli_exception(ValueError("missing credentials"))

    captured = capsys.readouterr()

    assert exc_info.value.exit_code == 1
    assert captured.err == "missing credentials\n"
    assert captured.out == ""


def test_validate_output_options_rejects_both_json_and_raw() -> None:
    with pytest.raises(typer.BadParameter) as exc_info:
        validate_output_options(json_output=True, raw_output=True)

    assert str(exc_info.value) == "Use only one of --json or --raw."
    assert exc_info.value.param_hint == "--json / --raw"
