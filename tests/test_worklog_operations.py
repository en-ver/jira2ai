from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from textwrap import dedent
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jira2ai_core.errors import Jira2AIValidationError
from jira2ai_core.formatters import format_worklog_report
from jira2ai_core.models import WorklogReport
from jira2ai_core.operations.worklogs import get_worklog_report


class SequentialMethod:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError(f"Unexpected extra call: {kwargs}")
        return deepcopy(self._responses.pop(0))


class RoutedMethod:
    def __init__(self, responses: dict[tuple[str, int], dict[str, object]]) -> None:
        self._responses = {key: deepcopy(value) for key, value in responses.items()}
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        key = (str(kwargs["issue_id"]), int(kwargs["start_at"]))
        if key not in self._responses:
            raise AssertionError(f"Unexpected call: {kwargs}")
        return deepcopy(self._responses[key])


def make_api(
    *,
    search_pages: list[dict[str, object]],
    worklog_pages: dict[tuple[str, int], dict[str, object]],
):
    search_method = SequentialMethod(search_pages)
    worklog_method = RoutedMethod(worklog_pages)
    return SimpleNamespace(
        search=SimpleNamespace(enhanced_search=search_method),
        worklogs=SimpleNamespace(get_worklogs=worklog_method),
        _search_method=search_method,
        _worklog_method=worklog_method,
    )


@pytest.mark.parametrize(
    ("start_date", "end_date", "message"),
    [
        ("2026/06/12", "2026-06-13", "start_date must be in YYYY-MM-DD format."),
        ("20260612", "2026-06-13", "start_date must be in YYYY-MM-DD format."),
        ("2026-W24-5", "2026-06-13", "start_date must be in YYYY-MM-DD format."),
        ("2026-13-12", "2026-06-13", "start_date must be in YYYY-MM-DD format."),
        ("2026-06-32", "2026-06-13", "start_date must be in YYYY-MM-DD format."),
        ("2026-06-12", "2026/06/13", "end_date must be in YYYY-MM-DD format."),
        ("2026-06-12", "20260613", "end_date must be in YYYY-MM-DD format."),
        ("2026-06-12", "2026-W24-6", "end_date must be in YYYY-MM-DD format."),
        ("2026-06-12", "2026-13-13", "end_date must be in YYYY-MM-DD format."),
        ("2026-06-12", "2026-06-33", "end_date must be in YYYY-MM-DD format."),
        ("2026-06-14", "2026-06-13", "end_date must be on or after start_date."),
    ],
)
def test_get_worklog_report_validates_date_inputs(
    start_date: str,
    end_date: str,
    message: str,
) -> None:
    with pytest.raises(Jira2AIValidationError, match=message):
        get_worklog_report(
            cast(Any, SimpleNamespace()),
            start_date=start_date,
            end_date=end_date,
            jql="project = PROJ",
        )


def test_get_worklog_report_validates_query_and_max_issues() -> None:
    with pytest.raises(Jira2AIValidationError, match="jql must not be empty"):
        get_worklog_report(
            cast(Any, SimpleNamespace()),
            start_date="2026-06-12",
            end_date="2026-06-13",
            jql="   ",
        )

    with pytest.raises(Jira2AIValidationError, match="max_issues must be at least 1"):
        get_worklog_report(
            cast(Any, SimpleNamespace()),
            start_date="2026-06-12",
            end_date="2026-06-13",
            jql="project = PROJ",
            max_issues=0,
        )


def test_get_worklog_report_paginates_filters_and_formats_details() -> None:
    api = make_api(
        search_pages=[
            {
                "issues": [
                    {
                        "id": "10001",
                        "key": "PROJ-1",
                        "fields": {
                            "summary": "First task",
                            "project": {"key": "PROJ", "name": "Project"},
                        },
                    }
                ],
                "nextPageToken": "tok-1",
                "total": 2,
            },
            {
                "issues": [
                    {
                        "id": "10002",
                        "key": "PROJ-2",
                        "fields": {
                            "summary": "Second task",
                            "project": {"key": "PROJ", "name": "Project"},
                        },
                    }
                ],
                "total": 2,
            },
        ],
        worklog_pages={
            ("10001", 0): {
                "startAt": 0,
                "total": 3,
                "worklogs": [
                    {
                        "id": "wl-1",
                        "issueId": "10001",
                        "author": {
                            "displayName": "Alice",
                            "accountId": "acct-1",
                            "active": True,
                        },
                        "updateAuthor": {
                            "displayName": "Reviewer",
                            "accountId": "acct-9",
                            "active": True,
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
                        "visibility": {"type": "role", "value": "Developers"},
                        "properties": [{"key": "tempo", "value": "billable"}],
                        "started": "2026-06-12T00:00:00.000+0000",
                        "created": "2026-06-12T00:05:00.000+0000",
                        "updated": "2026-06-12T00:10:00.000+0000",
                        "timeSpentSeconds": 3600,
                        "timeSpent": "1h",
                    }
                ],
            },
            ("10001", 1): {
                "startAt": 1,
                "total": 3,
                "worklogs": [
                    {
                        "id": "wl-2",
                        "issueId": "10001",
                        "author": {
                            "displayName": "Bob",
                            "accountId": "acct-2",
                            "active": True,
                        },
                        "started": "2026-06-12T09:00:00.000+0000",
                        "created": "2026-06-12T09:05:00.000+0000",
                        "updated": "2026-06-12T09:10:00.000+0000",
                        "timeSpentSeconds": 1800,
                        "timeSpent": "30m",
                    },
                    {
                        "id": "wl-0",
                        "issueId": "10001",
                        "author": {
                            "displayName": "Alice",
                            "accountId": "acct-1",
                            "active": True,
                        },
                        "started": "2026-06-11T23:59:59.000+0000",
                        "created": "2026-06-11T23:59:59.000+0000",
                        "updated": "2026-06-11T23:59:59.000+0000",
                        "timeSpentSeconds": 600,
                        "timeSpent": "10m",
                    },
                ],
            },
            ("10002", 0): {
                "startAt": 0,
                "total": 2,
                "worklogs": [
                    {
                        "id": "wl-3",
                        "issueId": "10002",
                        "author": {
                            "displayName": "Alice",
                            "accountId": "acct-1",
                            "active": True,
                        },
                        "started": "2026-06-13T23:59:59.000+0000",
                        "created": "2026-06-13T23:59:59.000+0000",
                        "updated": "2026-06-13T23:59:59.000+0000",
                        "timeSpentSeconds": 1800,
                        "timeSpent": "30m",
                    },
                    {
                        "id": "wl-4",
                        "issueId": "10002",
                        "author": {
                            "displayName": "Alice",
                            "accountId": "acct-1",
                            "active": True,
                        },
                        "started": "2026-06-14T00:00:00.000+0000",
                        "created": "2026-06-14T00:00:00.000+0000",
                        "updated": "2026-06-14T00:00:00.000+0000",
                        "timeSpentSeconds": 7200,
                        "timeSpent": "2h",
                    },
                ],
            },
        },
    )

    result = get_worklog_report(
        api,
        start_date="2026-06-12",
        end_date="2026-06-13",
        jql="project = PROJ",
        account_id="acct-1",
        max_issues=3,
        include_details=True,
    )

    start_dt = datetime(2026, 6, 12, tzinfo=UTC)
    end_dt = datetime(2026, 6, 14, tzinfo=UTC)
    start_ms = int(start_dt.timestamp() * 1000)
    expected_range = {
        "startedAfter": start_ms - 1,
        "startedBefore": int(end_dt.timestamp() * 1000),
    }

    assert expected_range["startedAfter"] < start_ms

    assert api._search_method.calls == [
        {
            "jql": "project = PROJ",
            "next_page_token": None,
            "max_results": 3,
            "fields": ["summary", "project"],
        },
        {
            "jql": "project = PROJ",
            "next_page_token": "tok-1",
            "max_results": 2,
            "fields": ["summary", "project"],
        },
    ]
    assert api._worklog_method.calls == [
        {
            "issue_id": "10001",
            "start_at": 0,
            "max_results": 5000,
            "extra_params": expected_range,
        },
        {
            "issue_id": "10001",
            "start_at": 1,
            "max_results": 5000,
            "extra_params": expected_range,
        },
        {
            "issue_id": "10002",
            "start_at": 0,
            "max_results": 5000,
            "extra_params": expected_range,
        },
    ]

    assert result.data == {
        "startDate": "2026-06-12",
        "endDate": "2026-06-13",
        "timezone": "UTC",
        "endDateInclusive": True,
        "startedAtOrAfter": "2026-06-12T00:00:00Z",
        "startedBefore": "2026-06-14T00:00:00Z",
        "accountId": "acct-1",
        "issueSelector": {
            "jql": "project = PROJ",
            "maxIssues": 3,
            "issuesReturned": 2,
            "truncated": False,
            "nextPageToken": None,
            "total": 2,
        },
        "rowCount": 2,
        "totalSeconds": 5400,
        "totalHours": 1.5,
        "rows": [
            {
                "dateTime": "2026-06-12T00:00:00Z",
                "issueId": "10001",
                "issueKey": "PROJ-1",
                "accountId": "acct-1",
                "displayName": "Alice",
                "timeSpentHours": 1.0,
                "worklogId": "wl-1",
                "issueSummary": "First task",
                "projectKey": "PROJ",
                "started": "2026-06-12T00:00:00Z",
                "created": "2026-06-12T00:05:00Z",
                "updated": "2026-06-12T00:10:00Z",
                "timeSpentSeconds": 3600,
                "timeSpent": "1h",
                "updateAuthor": {
                    "displayName": "Reviewer",
                    "accountId": "acct-9",
                    "active": True,
                },
                "visibility": {
                    "type": "role",
                    "value": "Developers",
                    "identifier": None,
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
                "properties": [{"key": "tempo", "value": "billable"}],
            },
            {
                "dateTime": "2026-06-13T23:59:59Z",
                "issueId": "10002",
                "issueKey": "PROJ-2",
                "accountId": "acct-1",
                "displayName": "Alice",
                "timeSpentHours": 0.5,
                "worklogId": "wl-3",
                "issueSummary": "Second task",
                "projectKey": "PROJ",
                "started": "2026-06-13T23:59:59Z",
                "created": "2026-06-13T23:59:59Z",
                "updated": "2026-06-13T23:59:59Z",
                "timeSpentSeconds": 1800,
                "timeSpent": "30m",
                "updateAuthor": None,
                "visibility": None,
                "comment": None,
                "properties": [],
            },
        ],
    }
    assert "Worklog report" in result.text
    assert "Rows: 2" in result.text
    assert "Total: 1.50h (5400s)" in result.text
    assert "updateAuthor: Reviewer (acct-9)" in result.text
    assert "visibility: role / Developers" in result.text
    assert "Finished the implementation" in result.text


def test_get_worklog_report_marks_issue_selector_truncation() -> None:
    api = make_api(
        search_pages=[
            {
                "issues": [
                    {
                        "id": "10001",
                        "key": "PROJ-1",
                        "fields": {
                            "summary": "First task",
                            "project": {"key": "PROJ", "name": "Project"},
                        },
                    }
                ],
                "nextPageToken": "tok-more",
                "total": 5,
            }
        ],
        worklog_pages={("10001", 0): {"startAt": 0, "total": 0, "worklogs": []}},
    )

    result = get_worklog_report(
        api,
        start_date="2026-06-12",
        end_date="2026-06-12",
        jql="project = PROJ",
        max_issues=1,
    )
    data = cast(dict[str, Any], result.data)

    assert api._search_method.calls == [
        {
            "jql": "project = PROJ",
            "next_page_token": None,
            "max_results": 1,
            "fields": ["summary", "project"],
        }
    ]
    assert data["issueSelector"] == {
        "jql": "project = PROJ",
        "maxIssues": 1,
        "issuesReturned": 1,
        "truncated": True,
        "nextPageToken": "tok-more",
        "total": 5,
    }
    assert (
        result.text
        == dedent(
            """\
        Worklog report
        Date range: 2026-06-12 to 2026-06-12 (UTC; end date inclusive)
        Account: all users
        JQL: project = PROJ
        Issues scanned: 1 (max 1, truncated)
        Rows: 0
        Total: 0.00h (0s)
        Issue search total: 5
        More issues matched the JQL but were not scanned.

        No matching worklogs found.
        """
        ).strip()
    )


def test_format_worklog_report_renders_expected_summary() -> None:
    report = WorklogReport.model_validate(
        {
            "startDate": "2026-06-12",
            "endDate": "2026-06-13",
            "timezone": "UTC",
            "endDateInclusive": True,
            "startedAtOrAfter": "2026-06-12T00:00:00Z",
            "startedBefore": "2026-06-14T00:00:00Z",
            "accountId": "acct-1",
            "issueSelector": {
                "jql": "project = PROJ",
                "maxIssues": 10,
                "issuesReturned": 1,
                "truncated": False,
            },
            "rowCount": 1,
            "totalSeconds": 3600,
            "totalHours": 1.0,
            "rows": [
                {
                    "dateTime": "2026-06-12T09:30:00Z",
                    "issueId": "10001",
                    "issueKey": "PROJ-1",
                    "accountId": "acct-1",
                    "displayName": "Alice",
                    "timeSpentHours": 1.0,
                    "worklogId": "wl-1",
                    "issueSummary": "First task",
                    "projectKey": "PROJ",
                    "started": "2026-06-12T09:30:00Z",
                    "created": "2026-06-12T09:35:00Z",
                    "updated": "2026-06-12T09:40:00Z",
                    "timeSpentSeconds": 3600,
                    "timeSpent": "1h",
                }
            ],
        }
    )

    assert (
        format_worklog_report(report)
        == dedent(
            """\
        Worklog report
        Date range: 2026-06-12 to 2026-06-13 (UTC; end date inclusive)
        Account: acct-1
        JQL: project = PROJ
        Issues scanned: 1 (max 10)
        Rows: 1
        Total: 1.00h (3600s)

        --- [ROWS (1)] ---
        - 2026-06-12T09:30:00Z — PROJ-1 — Alice (acct-1) — 1.00h
          issueId: 10001 | project: PROJ | summary: First task | worklogId: wl-1
          timeSpent: 1h / 3600s
          started: 2026-06-12T09:30:00Z
          created: 2026-06-12T09:35:00Z
          updated: 2026-06-12T09:40:00Z
        """
        ).strip()
    )
