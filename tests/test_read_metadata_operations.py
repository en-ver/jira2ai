from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2ai_core.errors import Jira2AIValidationError
from jira2ai_core.operations.comments import list_comments
from jira2ai_core.operations.fields import (
    get_create_fields,
    get_edit_fields,
    list_issue_types,
)
from jira2ai_core.operations.links import list_link_types
from jira2ai_core.operations.projects import list_projects
from jira2ai_core.operations.search import SEARCH_FIELDS, search_issues
from jira2ai_core.operations.users import search_users as search_users_operation
from jira2mcp.tools.comments import comments
from jira2mcp.tools.fields import fields
from jira2mcp.tools.link_types_resource import (
    list_link_types as list_link_types_resource,
)
from jira2mcp.tools.projects import projects
from jira2mcp.tools.search import search
from jira2mcp.tools.users import users


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


def make_api(
    *,
    search_response=None,
    comments_response=None,
    edit_metadata_response=None,
    issue_types_response=None,
    create_fields_response=None,
    projects_response=None,
    users_response=None,
    link_types_response=None,
    search_error: Exception | None = None,
    comments_error: Exception | None = None,
    edit_metadata_error: Exception | None = None,
    issue_types_error: Exception | None = None,
    create_fields_error: Exception | None = None,
    projects_error: Exception | None = None,
    users_error: Exception | None = None,
    link_types_error: Exception | None = None,
):
    methods = {
        "enhanced_search": RecordingMethod(
            response=search_response,
            error=search_error,
        ),
        "get_comments": RecordingMethod(
            response=comments_response,
            error=comments_error,
        ),
        "get_edit_metadata": RecordingMethod(
            response=edit_metadata_response,
            error=edit_metadata_error,
        ),
        "get_create_issue_types": RecordingMethod(
            response=issue_types_response,
            error=issue_types_error,
        ),
        "get_create_fields": RecordingMethod(
            response=create_fields_response,
            error=create_fields_error,
        ),
        "search_projects": RecordingMethod(
            response=projects_response,
            error=projects_error,
        ),
        "search_users": RecordingMethod(
            response=users_response,
            error=users_error,
        ),
        "get_link_types": RecordingMethod(
            response=link_types_response,
            error=link_types_error,
        ),
    }

    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        search=SimpleNamespace(enhanced_search=methods["enhanced_search"]),
        comments=SimpleNamespace(get_comments=methods["get_comments"]),
        issues=SimpleNamespace(
            get_edit_metadata=methods["get_edit_metadata"],
            get_create_issue_types=methods["get_create_issue_types"],
            get_create_fields=methods["get_create_fields"],
        ),
        projects=SimpleNamespace(search_projects=methods["search_projects"]),
        users=SimpleNamespace(search_users=methods["search_users"]),
        issue_links=SimpleNamespace(get_link_types=methods["get_link_types"]),
        _methods=methods,
    )


@pytest.fixture
def search_response() -> dict[str, object]:
    return {
        "issues": [
            {
                "key": "PROJ-101",
                "fields": {
                    "summary": "Ship the feature",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Alice"},
                },
            }
        ],
        "nextPageToken": "next-page",
    }


@pytest.fixture
def comments_response() -> dict[str, object]:
    return {
        "startAt": 1,
        "total": 3,
        "comments": [
            {
                "author": {"displayName": "Alice", "accountId": "123", "active": True},
                "created": "2026-01-02T03:04:05.000+0000",
                "updated": "2026-01-02T03:04:05.000+0000",
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Looks good"}],
                        }
                    ],
                },
            }
        ],
    }


@pytest.fixture
def issue_types_response() -> dict[str, object]:
    return {
        "values": [
            {"id": "10001", "name": "Bug", "subtask": False},
            {"id": "10002", "name": "Task", "subtask": False},
        ]
    }


@pytest.fixture
def create_fields_response() -> dict[str, object]:
    return {
        "values": [
            {
                "fieldId": "summary",
                "name": "Summary",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "fieldId": "customfield_10001",
                "name": "Acceptance Criteria",
                "required": False,
                "schema": {"type": "string", "custom": "textarea"},
            },
        ]
    }


@pytest.fixture
def edit_metadata_response() -> dict[str, object]:
    return {
        "fields": {
            "summary": {
                "name": "Summary",
                "required": True,
                "schema": {"type": "string"},
            },
            "customfield_10001": {
                "name": "Acceptance Criteria",
                "required": False,
                "schema": {"type": "string", "custom": "textarea"},
            },
        }
    }


@pytest.fixture
def projects_response() -> dict[str, object]:
    return {
        "values": [
            {"key": "PROJ", "name": "Project One"},
            {"key": "OPS", "name": "Operations"},
        ],
        "isLast": False,
        "total": 5,
    }


@pytest.fixture
def users_response() -> list[dict[str, object]]:
    return [
        {"displayName": "Alice", "accountId": "A-1", "active": True},
        {"displayName": "Bob", "accountId": "B-2", "active": False},
    ]


@pytest.fixture
def link_types_response() -> dict[str, object]:
    return {
        "issueLinkTypes": [
            {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"}
        ]
    }


def test_search_operation_formats_results_and_caps_max_results(
    search_response: dict[str, object],
) -> None:
    api = make_api(search_response=search_response)

    result = search_issues("project = PROJ", max_results=999, api=api)

    assert api._methods["enhanced_search"].calls == [
        {
            "jql": "project = PROJ",
            "max_results": 50,
            "fields": SEARCH_FIELDS,
        }
    ]
    assert result.data == search_response
    assert "Found 1 issue(s)" in result.text
    assert "PROJ-101 — Ship the feature [In Progress] (Alice)" in result.text
    assert "more results available" in result.text


def test_comments_operation_preserves_paging_text_and_raw_payload(
    comments_response: dict[str, object],
) -> None:
    api = make_api(comments_response=comments_response)

    result = list_comments("PROJ-123", start_at=1, max_results=200, api=api)

    assert api._methods["get_comments"].calls == [
        {
            "issue_id": "PROJ-123",
            "start_at": 1,
            "max_results": 100,
            "order_by": "created",
        }
    ]
    assert result.data == comments_response
    assert result.text.startswith("Comments on PROJ-123: showing 2–2 of 3")
    assert "### Alice — 2026-01-02" in result.text
    assert "Use start_at=2 to fetch the next page" in result.text


def test_fields_operations_return_mode_specific_raw_payloads(
    issue_types_response: dict[str, object],
    create_fields_response: dict[str, object],
    edit_metadata_response: dict[str, object],
) -> None:
    api = make_api(
        issue_types_response=issue_types_response,
        create_fields_response=create_fields_response,
        edit_metadata_response=edit_metadata_response,
    )

    issue_types_result = list_issue_types("PROJ", api=api)
    create_fields_result = get_create_fields("PROJ", "bug", api=api)
    edit_fields_result = get_edit_fields("PROJ-123", api=api)

    assert issue_types_result.data == issue_types_response["values"]
    assert "Issue types for PROJ:" in issue_types_result.text
    assert "• Bug (id: 10001)" in issue_types_result.text

    assert api._methods["get_create_fields"].calls == [
        {"project_id_or_key": "PROJ", "issue_type_id": "10001"}
    ]
    assert create_fields_result.data == create_fields_response["values"]
    assert "Fields for PROJ / Bug:" in create_fields_result.text
    assert 'customfield_10001 "Acceptance Criteria"' in create_fields_result.text

    assert edit_fields_result.data == edit_metadata_response
    assert "Fields for PROJ-123 / edit:" in edit_fields_result.text
    assert 'summary "Summary"' in edit_fields_result.text


def test_get_create_fields_raises_validation_error_for_unknown_issue_type(
    issue_types_response: dict[str, object],
) -> None:
    api = make_api(issue_types_response=issue_types_response)

    with pytest.raises(
        Jira2AIValidationError,
        match='Issue type "Epic" not found in PROJ. Available: Bug, Task',
    ):
        get_create_fields("PROJ", "Epic", api=api)


def test_projects_users_and_link_types_operations_format_current_output(
    projects_response: dict[str, object],
    users_response: list[dict[str, object]],
    link_types_response: dict[str, object],
) -> None:
    api = make_api(
        projects_response=projects_response,
        users_response=users_response,
        link_types_response=link_types_response,
    )

    projects_result = list_projects("pro", api=api)
    users_result = search_users_operation("ali", max_results=60, api=api)
    link_types_result = list_link_types(api=api)

    assert projects_result.data == projects_response
    assert 'Projects matching "pro":' in projects_result.text
    assert "... and 3 more (refine your search)" in projects_result.text

    assert api._methods["search_users"].calls == [{"query": "ali", "max_results": 50}]
    assert users_result.data == users_response
    assert users_result.text == (
        "Found 2 user(s):\n\n"
        "- Alice — accountId: A-1\n"
        "- Bob (inactive) — accountId: B-2"
    )

    assert link_types_result.data == link_types_response
    assert (
        link_types_result.text
        == '- **Blocks**: outward="blocks", inward="is blocked by"'
    )


def test_search_tool_uses_core_adapter_for_raw_output(
    fake_ctx,
    search_response: dict[str, object],
) -> None:
    api = make_api(search_response=search_response)

    result = asyncio.run(search("project = PROJ", raw=True, ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Searching issues: project = PROJ"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == search_response
    assert result.content[0].text == json.dumps(search_response, indent=2, default=str)


def test_comments_tool_uses_core_adapter_for_raw_output(
    fake_ctx,
    comments_response: dict[str, object],
) -> None:
    api = make_api(comments_response=comments_response)

    result = asyncio.run(comments("PROJ-123", raw=True, ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Fetching comments for PROJ-123"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == comments_response
    assert result.content[0].text == json.dumps(
        comments_response,
        indent=2,
        default=str,
    )


def test_fields_tool_create_mode_is_thin_adapter(
    fake_ctx,
    issue_types_response: dict[str, object],
    create_fields_response: dict[str, object],
) -> None:
    api = make_api(
        issue_types_response=issue_types_response,
        create_fields_response=create_fields_response,
    )

    result = asyncio.run(
        fields(
            project_key="PROJ",
            issue_type="bug",
            ctx=fake_ctx,
            api=api,
        )
    )

    assert fake_ctx.info_messages == [
        "Fetching issue types for PROJ",
        "Fetching create fields for PROJ/bug",
    ]
    assert fake_ctx.error_messages == []
    assert isinstance(result, str)
    assert "Fields for PROJ / Bug:" in result
    assert api._methods["get_create_issue_types"].calls == [
        {"project_id_or_key": "PROJ"}
    ]


def test_fields_tool_validation_is_mapped_without_logging(fake_ctx) -> None:
    api = make_api()

    with pytest.raises(
        ToolError,
        match=r"Provide either project_key \(to list issue types / create fields\) or issue_key \(to list edit fields\)\.",
    ):
        asyncio.run(fields(ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_projects_tool_logs_and_wraps_operation_errors(fake_ctx) -> None:
    api = make_api(projects_error=RuntimeError("boom"))

    with pytest.raises(ToolError, match=r"Failed to fetch projects: boom"):
        asyncio.run(projects(ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Fetching projects"]
    assert fake_ctx.error_messages == ["Failed to fetch projects: boom"]


def test_users_tool_and_link_types_resource_delegate_to_core(
    fake_ctx,
    users_response: list[dict[str, object]],
    link_types_response: dict[str, object],
) -> None:
    api = make_api(
        users_response=users_response,
        link_types_response=link_types_response,
    )

    users_result = asyncio.run(users("ali", ctx=fake_ctx, api=api))
    link_types_result = list_link_types_resource(api=api)

    assert fake_ctx.info_messages == ["Searching users: ali"]
    assert fake_ctx.error_messages == []
    assert users_result == (
        "Found 2 user(s):\n\n"
        "- Alice — accountId: A-1\n"
        "- Bob (inactive) — accountId: B-2"
    )
    assert link_types_result == '- **Blocks**: outward="blocks", inward="is blocked by"'
    assert list_link_types_resource.__name__ == "list_link_types"
