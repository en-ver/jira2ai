from __future__ import annotations

import asyncio
import inspect
import json
from textwrap import dedent
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools import ToolResult
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
    payload = {
        "issueSelector": {
            "jql": "project = PROJ",
            "maxIssues": 2,
            "issuesReturned": 2,
            "truncated": True,
            "nextPageToken": "tok-more",
            "total": 5,
        },
        "rowCount": 2,
        "rows": [
            {
                "issueKey": "PROJ-1",
                "updateAuthor": {
                    "displayName": "Reviewer",
                    "accountId": "acct-9",
                },
                "visibility": {
                    "type": "role",
                    "value": "Developers",
                },
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Finished the implementation",
                                }
                            ],
                        }
                    ],
                },
            },
            {"issueKey": "PROJ-2"},
        ],
    }

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
    rendered_payload = cast(Any, result.content[0]).text
    assert rendered_payload == json.dumps(payload, indent=2, default=str)
    assert '"truncated": true' in rendered_payload
    assert '"updateAuthor": {' in rendered_payload
    assert '"visibility": {' in rendered_payload
    assert '"comment": {' in rendered_payload


def test_worklog_report_preserves_formatted_multi_row_details_and_truncation(
    fake_ctx, monkeypatch
) -> None:
    formatted_report = dedent(
        """\
        Worklog report
        Date range: 2026-06-12 to 2026-06-13 (UTC; end date inclusive)
        Account: acct-1
        JQL: project = PROJ
        Issues scanned: 2 (max 2, truncated)
        Rows: 2
        Total: 1.50h (5400s)
        Issue search total: 5
        More issues matched the JQL but were not scanned.

        --- [ROWS (2)] ---
        - 2026-06-12T09:30:00Z — PROJ-1 — Alice (acct-1) — 1.00h
          issueId: 10001 | project: PROJ | summary: First task | worklogId: wl-1
          timeSpent: 1h / 3600s
          started: 2026-06-12T09:30:00Z
          created: 2026-06-12T09:35:00Z
          updated: 2026-06-12T09:40:00Z
          updateAuthor: Reviewer (acct-9)
          visibility: role / Developers
          comment: Finished the implementation
        - 2026-06-13T10:15:00Z — PROJ-2 — Bob (acct-2) — 0.50h
          issueId: 10002 | project: PROJ | summary: Second task | worklogId: wl-2
          timeSpent: 30m / 1800s
          started: 2026-06-13T10:15:00Z
          created: 2026-06-13T10:20:00Z
          updated: 2026-06-13T10:25:00Z
        """
    ).strip()

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.worklogs = cast(
                Any,
                type(
                    "Worklogs",
                    (),
                    {
                        "report": lambda _self, **_kwargs: HelperResult.text_only(
                            formatted_report
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
            account_id="acct-1",
            max_issues=2,
            include_details=True,
            ctx=fake_ctx,
            api=cast(Any, object()),
        )
    )

    assert fake_ctx.info_messages == ["Building worklog report for JQL: project = PROJ"]
    assert fake_ctx.error_messages == []
    assert result == formatted_report


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
