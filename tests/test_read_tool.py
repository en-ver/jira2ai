from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2mcp.tools.read import read
from jira2mcp.utils import TRUNCATION_SUFFIX
from jira2py import JiraError


def _tool_text(result: ToolResult) -> str:
    return cast(Any, result.content[0]).text


def test_read_returns_unmodified_structured_issue(
    fake_ctx,
    make_read_api,
    sample_issue_data: dict[str, object],
) -> None:
    api = make_read_api(issue_data=sample_issue_data)
    fields = ["summary", "customfield_10001", "*all", "-description", "summary"]

    result = asyncio.run(
        read(
            "PROJ-123",
            fields=fields,
            ctx=fake_ctx,
            api=api,
        )
    )

    assert fake_ctx.info_messages == ["Reading issue PROJ-123"]
    assert fake_ctx.error_messages == []
    assert api._get_issue.calls == [
        {
            "issue_id": "PROJ-123",
            "fields": fields,
        }
    ]
    assert isinstance(result, ToolResult)
    assert result.structured_content == sample_issue_data
    assert _tool_text(result) == json.dumps(
        sample_issue_data,
        separators=(",", ":"),
        default=str,
    )


def test_read_preserves_raw_mention_adf_for_identity_safe_edits(
    fake_ctx, make_read_api
) -> None:
    issue_data = {
        "key": "PROJ-123",
        "fields": {
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "mention", "attrs": {"id": "account-123"}}
                        ],
                    }
                ],
            }
        },
    }
    api = make_read_api(issue_data=issue_data)

    result = asyncio.run(
        read("PROJ-123", fields=["description"], ctx=fake_ctx, api=api)
    )

    assert result.structured_content == issue_data


def test_read_normalizes_issue_key_before_api(fake_ctx, make_read_api) -> None:
    api = make_read_api(issue_data={"key": "PROJ-123", "fields": {}})

    asyncio.run(read("  PROJ-123  ", fields=["summary"], ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Reading issue PROJ-123"]
    assert api._get_issue.calls == [
        {
            "issue_id": "PROJ-123",
            "fields": ["summary"],
        }
    ]


def test_read_does_not_truncate_structured_data(fake_ctx, make_read_api) -> None:
    payload = {"key": "PROJ-123", "fields": {"description": "x" * 30_001}}
    api = make_read_api(issue_data=payload)

    result = asyncio.run(
        read("PROJ-123", fields=["description"], ctx=fake_ctx, api=api)
    )

    assert isinstance(result, ToolResult)
    assert result.structured_content == payload
    assert len(_tool_text(result)) > 30_000
    assert TRUNCATION_SUFFIX not in _tool_text(result)


@pytest.mark.parametrize(
    ("issue_key", "fields"),
    [
        ("   ", ["summary"]),
        ("PROJ-123", []),
        ("PROJ-123", [""]),
        ("PROJ-123", ["   "]),
        ("PROJ-123", [" summary"]),
        ("PROJ-123", ["summary "]),
        ("PROJ-123", ["summary,status"]),
    ],
)
def test_read_rejects_invalid_input_before_api(
    fake_ctx,
    make_read_api,
    issue_key: str,
    fields: list[str],
) -> None:
    api = make_read_api(issue_data={"key": "PROJ-123", "fields": {}})

    with pytest.raises(ToolError):
        asyncio.run(read(issue_key, fields=fields, ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []
    assert api._get_issue.calls == []


def test_read_wraps_jira_errors_in_toolerror(fake_ctx, make_read_api) -> None:
    api = make_read_api(issue_data={}, error=JiraError("boom"))

    with pytest.raises(ToolError, match=r"Failed to fetch issue PROJ-404: boom"):
        asyncio.run(read("PROJ-404", fields=["summary"], ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Reading issue PROJ-404"]
    assert fake_ctx.error_messages == ["Failed to fetch issue PROJ-404: boom"]


def test_read_does_not_disguise_unexpected_errors(fake_ctx, make_read_api) -> None:
    api = make_read_api(issue_data={}, error=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(read("PROJ-404", fields=["summary"], ctx=fake_ctx, api=api))

    assert fake_ctx.error_messages == []
