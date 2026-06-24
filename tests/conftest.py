from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest


class FakeContext:
    def __init__(
        self,
        *,
        roots: list[object] | None = None,
        list_roots_error: Exception | None = None,
    ) -> None:
        self.info_messages: list[str] = []
        self.error_messages: list[str] = []
        self.roots = list(roots or [])
        self.list_roots_error = list_roots_error

    async def info(self, message: str) -> None:
        self.info_messages.append(message)

    async def error(self, message: str) -> None:
        self.error_messages.append(message)

    async def list_roots(self) -> list[object]:
        if self.list_roots_error is not None:
            raise self.list_roots_error
        return list(self.roots)


class RecordingMethod:
    def __init__(self, *, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return deepcopy(self.response)


@pytest.fixture
def fake_ctx() -> FakeContext:
    return FakeContext()


@pytest.fixture
def sample_issue_data() -> dict[str, object]:
    return {
        "key": "PROJ-123",
        "names": {"customfield_10001": "Acceptance Criteria"},
        "fields": {
            "summary": "Fix thing",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "created": "2026-01-02T03:04:05.000+0000",
            "updated": "2026-01-03T03:04:05.000+0000",
            "labels": ["backend", "urgent"],
            "components": [{"name": "API"}],
            "fixVersions": [{"name": "1.2.3"}],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Hello "},
                            {
                                "type": "text",
                                "text": "world",
                                "marks": [{"type": "strong"}],
                            },
                        ],
                    }
                ],
            },
            "comment": {"total": 2},
            "attachment": [
                {
                    "id": 7,
                    "filename": "debug.log",
                    "mimeType": "text/plain",
                    "size": 1536,
                }
            ],
            "subtasks": [
                {
                    "key": "PROJ-124",
                    "fields": {
                        "summary": "subtask summary",
                        "status": {"name": "To Do"},
                    },
                }
            ],
            "issuelinks": [
                {
                    "id": "55",
                    "type": {"inward": "is blocked by", "outward": "blocks"},
                    "outwardIssue": {
                        "key": "PROJ-200",
                        "fields": {
                            "summary": "linked issue",
                            "status": {"name": "Done"},
                        },
                    },
                }
            ],
            "customfield_10001": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Extra field"}],
                    }
                ],
            },
            "customfield_10002": {"foo": "bar"},
        },
    }


@pytest.fixture
def make_read_api():
    def _make_read_api(
        *, issue_data: dict[str, object], error: Exception | None = None
    ):
        get_issue = RecordingMethod(response=issue_data, error=error)
        return SimpleNamespace(
            credentials=SimpleNamespace(url="https://example.atlassian.net"),
            issues=SimpleNamespace(get_issue=get_issue),
            _get_issue=get_issue,
        )

    return _make_read_api


@pytest.fixture
def make_write_api():
    def _make_write_api(
        *,
        fields_response=None,
        create_response=None,
        edit_response=None,
        comment_response=None,
        fields_error: Exception | None = None,
        create_error: Exception | None = None,
        edit_error: Exception | None = None,
        comment_error: Exception | None = None,
        create_link_error: Exception | None = None,
        delete_link_error: Exception | None = None,
    ):
        methods = {
            "get_fields": RecordingMethod(
                response=fields_response,
                error=fields_error,
            ),
            "create_issue": RecordingMethod(
                response=create_response,
                error=create_error,
            ),
            "edit_issue": RecordingMethod(
                response=edit_response,
                error=edit_error,
            ),
            "add_comment": RecordingMethod(
                response=comment_response,
                error=comment_error,
            ),
            "create_link": RecordingMethod(error=create_link_error),
            "delete_link": RecordingMethod(error=delete_link_error),
        }
        return SimpleNamespace(
            credentials=SimpleNamespace(url="https://example.atlassian.net"),
            fields=SimpleNamespace(get_fields=methods["get_fields"]),
            issues=SimpleNamespace(
                create_issue=methods["create_issue"],
                edit_issue=methods["edit_issue"],
            ),
            comments=SimpleNamespace(add_comment=methods["add_comment"]),
            issue_links=SimpleNamespace(
                create_link=methods["create_link"],
                delete_link=methods["delete_link"],
            ),
            _methods=methods,
        )

    return _make_write_api


@pytest.fixture
def make_attachment_api():
    def _make_attachment_api(
        *,
        metadata_response=None,
        metadata_error: Exception | None = None,
        username: str = "user@example.com",
        api_token: str = "secret-token",
    ):
        get_attachment_metadata = RecordingMethod(
            response=metadata_response,
            error=metadata_error,
        )
        return SimpleNamespace(
            credentials=SimpleNamespace(
                url="https://example.atlassian.net",
                username=username,
                api_token=api_token,
            ),
            attachments=SimpleNamespace(
                get_attachment_metadata=get_attachment_metadata,
            ),
            _get_attachment_metadata=get_attachment_metadata,
        )

    return _make_attachment_api
