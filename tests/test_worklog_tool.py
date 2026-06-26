from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2mcp import mcp
from jira2mcp.tools import worklogs as worklog_tool_module
from jira2mcp.tools.worklogs import worklog_report
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import (
    JiraHelperError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)


def test_worklog_report_delegates_to_helper_group(fake_ctx, monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    api = cast(Any, object())

    class FakeJiraHelpers:
        def __init__(self, received_api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **kwargs: (
                            calls.append({"api": received_api, **kwargs})
                            or HelperResult.with_data(
                                "formatted worklog report", {"rowCount": 1}
                            )
                        )
                    },
                )(),
            )

    monkeypatch.setattr(worklog_tool_module, "JiraHelpers", FakeJiraHelpers)

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

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **_kwargs: HelperResult.with_data(
                            "formatted worklog report", payload
                        )
                    },
                )(),
            )

    monkeypatch.setattr(worklog_tool_module, "JiraHelpers", FakeJiraHelpers)

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
    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **_kwargs: (_ for _ in ()).throw(
                            JiraHelperValidationError(
                                "start_date must be in YYYY-MM-DD format."
                            )
                        )
                    },
                )(),
            )

    monkeypatch.setattr(worklog_tool_module, "JiraHelpers", FakeJiraHelpers)

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
    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **_kwargs: (_ for _ in ()).throw(
                            JiraHelperOperationError(
                                "Failed to search issues for worklog report: boom"
                            )
                        )
                    },
                )(),
            )

    monkeypatch.setattr(worklog_tool_module, "JiraHelpers", FakeJiraHelpers)

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


def test_worklog_report_wraps_base_helper_errors_without_logging(
    fake_ctx, monkeypatch
) -> None:
    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **_kwargs: (_ for _ in ()).throw(
                            JiraHelperError("helper boom")
                        )
                    },
                )(),
            )

    monkeypatch.setattr(worklog_tool_module, "JiraHelpers", FakeJiraHelpers)

    with pytest.raises(ToolError, match=r"helper boom"):
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
    assert fake_ctx.error_messages == []


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
