from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2ai_core.errors import Jira2AIValidationError, JiraOperationError
from jira2ai_core.results import OperationResult
from jira2mcp import mcp
from jira2mcp.tools import worklogs as worklog_tool_module
from jira2mcp.tools.worklogs import worklog_report


def test_worklog_report_delegates_to_core_operation(fake_ctx, monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    api = cast(Any, object())

    def fake_get_worklog_report(
        *,
        api: object,
        start_date: str,
        end_date: str,
        jql: str,
        account_id: str | None = None,
        max_issues: int = 100,
        include_details: bool = False,
    ) -> OperationResult:
        calls.append(
            {
                "api": api,
                "start_date": start_date,
                "end_date": end_date,
                "jql": jql,
                "account_id": account_id,
                "max_issues": max_issues,
                "include_details": include_details,
            }
        )
        return OperationResult.with_data("formatted worklog report", {"rowCount": 1})

    monkeypatch.setattr(
        worklog_tool_module, "get_worklog_report", fake_get_worklog_report
    )

    result = asyncio.run(
        worklog_report(
            "2026-06-12",
            "2026-06-13",
            "issue = PROJ-123",
            account_id="acct-1",
            max_issues=25,
            include_details=True,
            ctx=fake_ctx,
            api=api,
        )
    )

    assert calls == [
        {
            "api": api,
            "start_date": "2026-06-12",
            "end_date": "2026-06-13",
            "jql": "issue = PROJ-123",
            "account_id": "acct-1",
            "max_issues": 25,
            "include_details": True,
        }
    ]
    assert fake_ctx.info_messages == [
        "Building worklog report for JQL: issue = PROJ-123"
    ]
    assert fake_ctx.error_messages == []
    assert result == "formatted worklog report"


def test_worklog_report_raw_returns_tool_result(fake_ctx, monkeypatch) -> None:
    payload = {"rowCount": 1, "rows": [{"issueKey": "PROJ-1"}]}

    def fake_get_worklog_report(**_: object) -> OperationResult:
        return OperationResult.with_data("formatted worklog report", payload)

    monkeypatch.setattr(
        worklog_tool_module, "get_worklog_report", fake_get_worklog_report
    )

    result = asyncio.run(
        worklog_report(
            "2026-06-12",
            "2026-06-13",
            "project = PROJ",
            raw=True,
            ctx=fake_ctx,
            api=cast(Any, object()),
        )
    )

    assert fake_ctx.info_messages == ["Building worklog report for JQL: project = PROJ"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == payload
    assert cast(Any, result.content[0]).text == json.dumps(
        payload, indent=2, default=str
    )


def test_worklog_report_wraps_validation_errors(fake_ctx, monkeypatch) -> None:
    def fake_get_worklog_report(**_: object) -> OperationResult:
        raise Jira2AIValidationError("start_date must be in YYYY-MM-DD format.")

    monkeypatch.setattr(
        worklog_tool_module, "get_worklog_report", fake_get_worklog_report
    )

    with pytest.raises(ToolError, match=r"start_date must be in YYYY-MM-DD format\."):
        asyncio.run(
            worklog_report(
                "2026/06/12",
                "2026-06-13",
                "project = PROJ",
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == ["Building worklog report for JQL: project = PROJ"]
    assert fake_ctx.error_messages == []


def test_worklog_report_logs_operation_errors(fake_ctx, monkeypatch) -> None:
    def fake_get_worklog_report(**_: object) -> OperationResult:
        raise JiraOperationError("Failed to search issues for worklog report: boom")

    monkeypatch.setattr(
        worklog_tool_module, "get_worklog_report", fake_get_worklog_report
    )

    with pytest.raises(
        ToolError,
        match=r"Failed to search issues for worklog report: boom",
    ):
        asyncio.run(
            worklog_report(
                "2026-06-12",
                "2026-06-13",
                "project = PROJ",
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == ["Building worklog report for JQL: project = PROJ"]
    assert fake_ctx.error_messages == [
        "Failed to search issues for worklog report: boom"
    ]


def test_worklog_report_signature_is_jql_only() -> None:
    parameter_names = list(inspect.signature(worklog_report).parameters)

    assert parameter_names == [
        "start_date",
        "end_date",
        "jql",
        "account_id",
        "max_issues",
        "include_details",
        "raw",
        "ctx",
        "api",
    ]
    forbidden = {
        "issue",
        "issue_id",
        "issue_key",
        "issue_id_or_key",
        "task_id",
        "task_key",
    }
    assert forbidden.isdisjoint(parameter_names)


def test_worklog_report_tool_is_registered_with_expected_public_schema() -> None:
    registered_tools = asyncio.run(mcp.list_tools(run_middleware=False))
    tool = next(tool for tool in registered_tools if tool.name == "jira_worklog_report")
    parameters = tool.parameters
    properties = cast(dict[str, Any], parameters["properties"])
    required = set(cast(list[str], parameters["required"]))

    assert required == {"start_date", "end_date", "jql"}
    assert set(properties) == {
        "start_date",
        "end_date",
        "jql",
        "account_id",
        "max_issues",
        "include_details",
        "raw",
    }
    forbidden = {
        "issue",
        "issue_id",
        "issue_key",
        "issue_id_or_key",
        "task_id",
        "task_key",
    }
    assert forbidden.isdisjoint(properties)
