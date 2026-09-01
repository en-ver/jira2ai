from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastmcp.tools.tool import ToolResult
from jira2mcp.tools import transitions as transitions_tool_module
from jira2mcp.tools.transitions import transition, transitions
from jira2py.helpers import HelperResult


class FakeJiraHelpers:
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def __init__(self, _api: object) -> None:
        self.metadata = SimpleNamespace(transitions=self._transitions)
        self.issues = SimpleNamespace(transition=self._transition)

    @classmethod
    def _transitions(cls, issue_key: str, **kwargs: object) -> HelperResult:
        cls.calls.append(("transitions", (issue_key,), kwargs))
        return HelperResult.with_data(
            "available transitions",
            {"transitions": [{"id": "31", "fields": {"resolution": {}}}]},
        )

    @classmethod
    def _transition(
        cls,
        issue_key: str,
        transition_id: str,
        **kwargs: object,
    ) -> HelperResult:
        cls.calls.append(("transition", (issue_key, transition_id), kwargs))
        return HelperResult.with_data(
            "Jira accepted transition without a verification read",
            {
                "issue_key": issue_key,
                "transition_id": transition_id,
                "verified": False,
            },
        )


@pytest.fixture
def fake_helpers(monkeypatch: pytest.MonkeyPatch) -> type[FakeJiraHelpers]:
    FakeJiraHelpers.calls = []
    monkeypatch.setattr(transitions_tool_module, "JiraHelpers", FakeJiraHelpers)
    return FakeJiraHelpers


def test_transitions_tool_forwards_focused_discovery_options(
    fake_ctx,
    fake_helpers: type[FakeJiraHelpers],
) -> None:
    result = asyncio.run(
        transitions(
            "PROJ-1",
            transition_id="31",
            include_unavailable_transitions=True,
            raw=True,
            ctx=fake_ctx,
            api=cast(Any, object()),
        )
    )

    assert fake_helpers.calls == [
        (
            "transitions",
            ("PROJ-1",),
            {"transition_id": "31", "include_unavailable_transitions": True},
        )
    ]
    assert fake_ctx.info_messages == ["Fetching transitions for PROJ-1"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == {
        "transitions": [{"id": "31", "fields": {"resolution": {}}}]
    }


def test_transition_tool_forwards_native_bodies_without_echoing_them(
    fake_ctx,
    fake_helpers: type[FakeJiraHelpers],
) -> None:
    fields = {"resolution": {"name": "sensitive-field-value"}}
    update = {
        "comment": [
            {
                "add": {
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [{"type": "paragraph", "content": []}],
                        "private": "sensitive-body-value",
                    }
                }
            }
        ]
    }

    result = asyncio.run(
        transition(
            "PROJ-1",
            "31",
            fields=fields,
            update=update,
            ctx=fake_ctx,
            api=cast(Any, object()),
        )
    )

    assert fake_helpers.calls == [
        ("transition", ("PROJ-1", "31"), {"fields": fields, "update": update})
    ]
    assert result == "Jira accepted transition without a verification read"
    logged_output = "\n".join([*fake_ctx.info_messages, *fake_ctx.error_messages])
    assert logged_output == "Transitioning PROJ-1 via 31"
    assert "sensitive-field-value" not in logged_output
    assert "sensitive-body-value" not in logged_output
    assert "sensitive-field-value" not in result
    assert "sensitive-body-value" not in result
