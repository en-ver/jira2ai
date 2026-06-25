from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2mcp.tools.read import read
from jira2py.helpers.issues import DEFAULT_FIELDS


def test_read_returns_formatted_issue_and_merges_extra_fields(
    fake_ctx,
    make_read_api,
    sample_issue_data: dict[str, object],
) -> None:
    api = make_read_api(issue_data=sample_issue_data)

    result = asyncio.run(
        read(
            "PROJ-123",
            extra_fields=["customfield_10001", "customfield_10002", "summary"],
            ctx=fake_ctx,
            api=api,
        )
    )

    assert fake_ctx.info_messages == ["Reading issue PROJ-123"]
    assert fake_ctx.error_messages == []
    assert api._get_issue.calls == [
        {
            "issue_id": "PROJ-123",
            "fields": ",".join(
                [*DEFAULT_FIELDS, "customfield_10001", "customfield_10002"]
            ),
            "expand": "names",
        }
    ]
    assert isinstance(result, str)
    assert "Key: PROJ-123" in result
    assert "URL: https://example.atlassian.net/browse/PROJ-123" in result
    assert "Comments: 2" in result
    assert "--- [ATTACHMENTS (1)] ---" in result
    assert "--- [ADDITIONAL FIELDS] ---" in result
    assert "--- [ACCEPTANCE CRITERIA (CUSTOMFIELD_10001)] ---" in result


def test_read_raw_returns_tool_result(
    fake_ctx,
    make_read_api,
    sample_issue_data: dict[str, object],
) -> None:
    api = make_read_api(issue_data=sample_issue_data)

    result = asyncio.run(read("PROJ-123", raw=True, ctx=fake_ctx, api=api))

    assert isinstance(result, ToolResult)
    assert result.structured_content == sample_issue_data
    assert len(result.content) == 1
    assert cast(Any, result.content[0]).text == json.dumps(
        sample_issue_data, indent=2, default=str
    )


def test_read_wraps_api_errors_in_toolerror(fake_ctx, make_read_api) -> None:
    api = make_read_api(issue_data={}, error=RuntimeError("boom"))

    with pytest.raises(ToolError, match=r"Failed to fetch issue PROJ-404: boom"):
        asyncio.run(read("PROJ-404", ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Reading issue PROJ-404"]
    assert fake_ctx.error_messages == ["Failed to fetch issue PROJ-404: boom"]
