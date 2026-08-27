from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2mcp import mcp
from jira2mcp.tools import changelogs as changelog_tool_module
from jira2mcp.tools.changelogs import changelogs, changelogs_by_ids
from jira2mcp.utils import TRUNCATION_SUFFIX
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError


def test_changelogs_delegates_complete_history_and_filters(
    fake_ctx, monkeypatch
) -> None:
    calls: list[tuple[str, object]] = []
    api = cast(Any, object())

    class FakeJiraHelpers:
        def __init__(self, received_api: object) -> None:
            self.changelogs = cast(
                Any,
                type(
                    "Changelogs",
                    (),
                    {
                        "list": lambda _self, issue_key, **kwargs: (
                            calls.append(("list", (received_api, issue_key, kwargs)))
                            or HelperResult.text_only("formatted changelogs")
                        )
                    },
                )(),
            )

    monkeypatch.setattr(changelog_tool_module, "JiraHelpers", FakeJiraHelpers)

    result = asyncio.run(
        changelogs(
            "PROJ-123",
            created_at_or_after="2026-08-01T00:00:00Z",
            created_before="2026-09-01T00:00:00Z",
            ctx=fake_ctx,
            api=api,
        )
    )

    assert result == "formatted changelogs"
    assert calls == [
        (
            "list",
            (
                api,
                "PROJ-123",
                {
                    "created_at_or_after": "2026-08-01T00:00:00Z",
                    "created_before": "2026-09-01T00:00:00Z",
                },
            ),
        )
    ]
    assert fake_ctx.info_messages == [
        "Fetching complete changelog history for PROJ-123"
    ]
    assert fake_ctx.error_messages == []


def test_changelogs_by_ids_forwards_native_ids_and_raw_envelope(
    fake_ctx, monkeypatch
) -> None:
    payload = {"issue_key": "PROJ-123", "changelogs": [{"id": "10002"}]}
    calls: list[tuple[str, list[int]]] = []

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.changelogs = cast(
                Any,
                type(
                    "Changelogs",
                    (),
                    {
                        "list_by_ids": lambda _self, issue_key, changelog_ids: (
                            calls.append((issue_key, changelog_ids))
                            or HelperResult.with_data("formatted changelogs", payload)
                        )
                    },
                )(),
            )

    monkeypatch.setattr(changelog_tool_module, "JiraHelpers", FakeJiraHelpers)

    result = asyncio.run(
        changelogs_by_ids(
            "PROJ-123",
            [10002, 10001, 10002],
            raw=True,
            ctx=fake_ctx,
            api=cast(Any, object()),
        )
    )

    assert calls == [("PROJ-123", [10002, 10001, 10002])]
    assert fake_ctx.info_messages == ["Fetching known changelog IDs for PROJ-123"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == payload
    assert cast(Any, result.content[0]).text == json.dumps(
        payload, indent=2, default=str
    )


def test_changelogs_truncates_normal_text(fake_ctx, monkeypatch) -> None:
    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.changelogs = cast(
                Any,
                type(
                    "Changelogs",
                    (),
                    {
                        "list": lambda _self, *_args, **_kwargs: HelperResult.text_only(
                            "x" * 30_001
                        )
                    },
                )(),
            )

    monkeypatch.setattr(changelog_tool_module, "JiraHelpers", FakeJiraHelpers)

    result = asyncio.run(changelogs("PROJ-123", ctx=fake_ctx, api=cast(Any, object())))

    assert isinstance(result, str)
    assert result.endswith(TRUNCATION_SUFFIX)


def test_changelog_tools_map_helper_errors_with_expected_logging(
    fake_ctx, monkeypatch
) -> None:
    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.changelogs = cast(
                Any,
                type(
                    "Changelogs",
                    (),
                    {
                        "list": lambda _self, *_args, **_kwargs: (_ for _ in ()).throw(
                            JiraHelperOperationError("history request failed")
                        ),
                        "list_by_ids": lambda _self, *_args, **_kwargs: (
                            _ for _ in ()
                        ).throw(JiraHelperValidationError("invalid changelog IDs")),
                    },
                )(),
            )

    monkeypatch.setattr(changelog_tool_module, "JiraHelpers", FakeJiraHelpers)

    with pytest.raises(ToolError, match="history request failed"):
        asyncio.run(changelogs("PROJ-123", ctx=fake_ctx, api=cast(Any, object())))
    with pytest.raises(ToolError, match="invalid changelog IDs"):
        asyncio.run(
            changelogs_by_ids(
                "PROJ-123",
                [10001],
                ctx=fake_ctx,
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.error_messages == ["history request failed"]


def test_changelogs_by_ids_rejects_strings_and_booleans_at_mcp_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[int]] = []

    class FakeJiraHelpers:
        def __init__(self, _api: object) -> None:
            self.changelogs = cast(
                Any,
                type(
                    "Changelogs",
                    (),
                    {
                        "list_by_ids": lambda _self, _issue_key, changelog_ids: (
                            calls.append(changelog_ids)
                            or HelperResult.text_only("formatted changelogs")
                        )
                    },
                )(),
            )

    monkeypatch.setattr(changelog_tool_module, "JiraHelpers", FakeJiraHelpers)
    api_dependency = changelogs_by_ids.__defaults__[-1]
    monkeypatch.setattr(api_dependency, "factory", lambda: object())

    async def scenario() -> None:
        async with Client(mcp) as client:
            for invalid_ids in (["10001"], [True]):
                result = await client.call_tool_mcp(
                    "jira_changelogs_by_ids",
                    {"issue_key": "PROJ-123", "changelog_ids": invalid_ids},
                )
                assert result.isError

            result = await client.call_tool_mcp(
                "jira_changelogs_by_ids",
                {"issue_key": "PROJ-123", "changelog_ids": [10001]},
            )
            assert not result.isError

    asyncio.run(scenario())

    assert calls == [[10001]]
