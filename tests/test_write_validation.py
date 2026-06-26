from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from jira2mcp.tools import create as create_tool_module
from jira2mcp.tools import edit as edit_tool_module
from jira2mcp.tools.create import create
from jira2mcp.tools.edit import edit
from jira2py.helpers.errors import JiraHelperError


def test_create_rejects_reserved_fields_in_fields_payload(fake_ctx) -> None:
    with pytest.raises(
        ToolError,
        match=r"Use explicit parameters instead of fields for: project",
    ):
        asyncio.run(
            create(
                "PROJ",
                "Bug",
                "Fix thing",
                fields={"project": {"key": "OTHER"}},
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_edit_requires_at_least_one_update(fake_ctx) -> None:
    with pytest.raises(
        ToolError,
        match=(
            "Nothing to update. Provide at least one of: summary, description, or fields."
        ),
    ):
        asyncio.run(edit("PROJ-123", ctx=fake_ctx, api=cast(Any, object())))

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_edit_rejects_reserved_fields_in_fields_payload(fake_ctx) -> None:
    with pytest.raises(
        ToolError,
        match=r"Use explicit parameters instead of fields for: summary",
    ):
        asyncio.run(
            edit(
                "PROJ-123",
                fields={"summary": "Renamed outside explicit param"},
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_create_wraps_base_helper_errors_from_validation(fake_ctx, monkeypatch) -> None:
    class FakeIssues:
        def validate_create(self, *_args, **_kwargs) -> None:
            raise JiraHelperError("helper boom")

        def create(self, *_args, **_kwargs) -> None:
            raise AssertionError("create should not be called")

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.issues = FakeIssues()

    monkeypatch.setattr(create_tool_module, "JiraHelpers", FakeJiraHelpers)

    with pytest.raises(ToolError, match=r"helper boom"):
        asyncio.run(
            create(
                "PROJ",
                "Bug",
                "Fix thing",
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_edit_wraps_base_helper_errors_without_logging(fake_ctx, monkeypatch) -> None:
    class FakeIssues:
        def validate_edit(self, *_args, **_kwargs) -> None:
            return None

        def edit(self, *_args, **_kwargs) -> None:
            raise JiraHelperError("helper boom")

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.issues = FakeIssues()

    monkeypatch.setattr(edit_tool_module, "JiraHelpers", FakeJiraHelpers)

    with pytest.raises(ToolError, match=r"helper boom"):
        asyncio.run(
            edit(
                "PROJ-123",
                summary="Updated",
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == ["Updating issue PROJ-123"]
    assert fake_ctx.error_messages == []
