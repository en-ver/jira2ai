from __future__ import annotations

import asyncio

import pytest
from fastmcp.exceptions import ToolError
from jira2mcp.tools.create import create
from jira2mcp.tools.edit import edit


def test_create_rejects_reserved_fields_in_fields_payload(fake_ctx) -> None:
    with pytest.raises(
        ToolError,
        match=r"Use explicit parameters instead of fields for: \{'project'\}",
    ):
        asyncio.run(
            create(
                "PROJ",
                "Bug",
                "Fix thing",
                fields={"project": {"key": "OTHER"}},
                ctx=fake_ctx,
                api=object(),
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
        asyncio.run(edit("PROJ-123", ctx=fake_ctx, api=object()))

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_edit_rejects_reserved_fields_in_fields_payload(fake_ctx) -> None:
    with pytest.raises(
        ToolError,
        match=r"Use explicit parameters instead of fields for: \{'summary'\}",
    ):
        asyncio.run(
            edit(
                "PROJ-123",
                fields={"summary": "Renamed outside explicit param"},
                ctx=fake_ctx,
                api=object(),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []
