from __future__ import annotations

from typing import Any

import jira2mcp
from jira2mcp import utils as mcp_utils


class FakeJiraAPI:
    def __init__(self, *, credentials_file=None) -> None:
        self.credentials_file = credentials_file


def test_get_api_uses_explicit_credentials_file(monkeypatch) -> None:
    monkeypatch.setattr(mcp_utils, "JiraAPI", FakeJiraAPI)
    mcp_utils.set_credentials_file("/tmp/jira-creds.json")

    api = mcp_utils.get_api()

    assert isinstance(api, FakeJiraAPI)
    assert api.credentials_file == "/tmp/jira-creds.json"
    mcp_utils.set_credentials_file(None)


def test_get_api_defaults_to_env_based_credentials_when_no_file(monkeypatch) -> None:
    monkeypatch.setattr(mcp_utils, "JiraAPI", FakeJiraAPI)
    mcp_utils.set_credentials_file(None)

    api = mcp_utils.get_api()

    assert isinstance(api, FakeJiraAPI)
    assert api.credentials_file is None


def test_main_accepts_credentials_file_flag(monkeypatch) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setattr(
        jira2mcp,
        "set_credentials_file",
        lambda path: recorded.setdefault("credentials_file", path),
    )
    monkeypatch.setattr(
        jira2mcp.mcp,
        "run",
        lambda **kwargs: recorded.setdefault("run_kwargs", kwargs),
    )

    jira2mcp.main(["--credentials-file", "/tmp/jira-creds.json"])

    assert recorded == {
        "credentials_file": "/tmp/jira-creds.json",
        "run_kwargs": {"transport": "stdio"},
    }


def test_main_preserves_env_only_launch_when_flag_omitted(monkeypatch) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setattr(
        jira2mcp,
        "set_credentials_file",
        lambda path: recorded.setdefault("credentials_file", path),
    )
    monkeypatch.setattr(
        jira2mcp.mcp,
        "run",
        lambda **kwargs: recorded.setdefault("run_kwargs", kwargs),
    )

    jira2mcp.main([])

    assert recorded == {
        "credentials_file": None,
        "run_kwargs": {"transport": "stdio"},
    }
