from __future__ import annotations

import json

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2ai_core.errors import Jira2AIValidationError
from jira2ai_core.results import OperationResult
from jira2mcp.adapter import adapt_operation_result, to_tool_error, to_tool_result


def test_adapt_operation_result_returns_plain_text_for_text_only_results() -> None:
    result = OperationResult.text_only("formatted output")

    adapted = adapt_operation_result(result)

    assert adapted == "formatted output"


def test_adapt_operation_result_returns_tool_result_for_raw_structured_data() -> None:
    payload = {"key": "PROJ-123", "labels": ["backend", "urgent"]}
    result = OperationResult.with_data("formatted output", payload)

    adapted = adapt_operation_result(result, raw=True)

    assert isinstance(adapted, ToolResult)
    assert adapted.structured_content == payload
    assert len(adapted.content) == 1
    assert adapted.content[0].text == json.dumps(payload, indent=2, default=str)


def test_adapt_operation_result_prefers_explicit_raw_content() -> None:
    result = OperationResult.with_data(
        "formatted output",
        {"key": "PROJ-123"},
        raw_content='{"custom":true}',
    )

    adapted = adapt_operation_result(result, raw=True)

    assert isinstance(adapted, ToolResult)
    assert adapted.structured_content == {"key": "PROJ-123"}
    assert adapted.content[0].text == '{"custom":true}'


def test_to_tool_result_rejects_text_only_results() -> None:
    with pytest.raises(ValueError, match="does not contain raw output"):
        to_tool_result(OperationResult.text_only("formatted output"))


def test_to_tool_error_maps_core_errors_to_fastmcp_toolerror() -> None:
    error = Jira2AIValidationError("missing project key")

    adapted = to_tool_error(error)

    assert isinstance(adapted, ToolError)
    assert str(adapted) == "missing project key"
