from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import jira2cli.cli as cli_module
import pytest
from jira2cli import app
from jira2cli import client as cli_client
from jira2py.helpers import HelperResult
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()


class FakeJiraAPI:
    def __init__(self, *, credentials_file=None) -> None:
        self.credentials_file = credentials_file


def _get_registered_command(command_name: str):
    return cast(Any, get_command(app)).commands[command_name]


def _patch_helpers(monkeypatch: pytest.MonkeyPatch, module_path: str, **groups) -> None:
    monkeypatch.setattr(
        f"{module_path}.JiraHelpers",
        lambda _api: SimpleNamespace(
            **{name: SimpleNamespace(**methods) for name, methods in groups.items()}
        ),
    )


def test_get_api_uses_explicit_credentials_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_client, "JiraAPI", FakeJiraAPI)
    cli_client.set_credentials_file("/tmp/jira-creds.json")

    api = cli_client.get_api()

    assert isinstance(api, FakeJiraAPI)
    assert api.credentials_file == "/tmp/jira-creds.json"
    cli_client.set_credentials_file(None)


def test_get_api_defaults_to_env_based_credentials_when_no_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_client, "JiraAPI", FakeJiraAPI)
    cli_client.set_credentials_file(None)

    api = cli_client.get_api()

    assert isinstance(api, FakeJiraAPI)
    assert api.credentials_file is None


def test_root_help_lists_stage9_commands_and_credentials_flag() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--credentials-file" in result.stdout
    for command_name in [
        "auth-status",
        "me",
        "transitions",
        "transition",
        "comment-update",
        "comment-delete",
        "attachment-list",
        "attachment-read",
        "attachment-download",
        "attachment-upload",
        "attachment-delete",
        "issue-links",
        "worklogs",
        "worklog-add",
        "worklog-update",
        "worklog-delete",
        "project",
        "statuses",
        "priorities",
        "filters",
        "filter-run",
    ]:
        assert command_name in result.stdout


def test_callback_accepts_credentials_file_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setattr(
        cli_module,
        "set_credentials_file",
        lambda path: recorded.setdefault("credentials_file", path),
    )

    result = runner.invoke(
        app,
        ["--credentials-file", "/tmp/jira-creds.json", "jql-syntax"],
    )

    assert result.exit_code == 0
    assert recorded == {"credentials_file": "/tmp/jira-creds.json"}


def test_callback_preserves_env_only_launch_when_flag_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setattr(
        cli_module,
        "set_credentials_file",
        lambda path: recorded.setdefault("credentials_file", path),
    )

    result = runner.invoke(app, ["jql-syntax"])

    assert result.exit_code == 0
    assert recorded == {"credentials_file": None}


def test_auth_commands_delegate_to_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.auth",
        auth={
            "status": lambda: (
                calls.append(("status", None)) or HelperResult.text_only("auth ok")
            ),
            "me": lambda: (
                calls.append(("me", None))
                or HelperResult.with_data("ignored", {"accountId": "acct-1"})
            ),
        },
    )

    status_result = runner.invoke(app, ["auth-status"])
    me_result = runner.invoke(app, ["me", "--json"])

    assert status_result.exit_code == 0
    assert status_result.stdout == "auth ok\n"
    assert me_result.exit_code == 0
    assert me_result.stdout == '{\n  "accountId": "acct-1"\n}\n'
    assert calls == [
        ("get_api", None),
        ("status", None),
        ("get_api", None),
        ("me", None),
    ]


def test_transition_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.transitions",
        metadata={
            "transitions": lambda issue_key: (
                calls.append(("transitions", issue_key))
                or HelperResult.text_only("available transitions")
            )
        },
        issues={
            "transition": lambda issue_key, transition: (
                calls.append(("transition", (issue_key, transition)))
                or HelperResult.with_data(
                    "ignored",
                    {"issue_key": issue_key, "transition": transition},
                )
            )
        },
    )

    transitions_result = runner.invoke(app, ["transitions", "PROJ-1"])
    transition_result = runner.invoke(
        app,
        ["transition", "PROJ-1", "Done", "--raw"],
    )

    assert transitions_result.exit_code == 0
    assert transitions_result.stdout == "available transitions\n"
    assert transition_result.exit_code == 0
    assert transition_result.stdout == (
        '{\n  "issue_key": "PROJ-1",\n  "transition": "Done"\n}\n'
    )
    assert calls == [
        ("get_api", None),
        ("transitions", "PROJ-1"),
        ("get_api", None),
        ("transition", ("PROJ-1", "Done")),
    ]


def test_comment_mutation_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.write",
        comments={
            "update": lambda issue_key, comment_id, body: (
                calls.append(("update", (issue_key, comment_id, body)))
                or HelperResult.text_only("comment updated")
            ),
            "delete": lambda issue_key, comment_id: (
                calls.append(("delete", (issue_key, comment_id)))
                or HelperResult.with_data(
                    "ignored",
                    {"issue_key": issue_key, "comment_id": comment_id},
                )
            ),
        },
    )

    update_result = runner.invoke(
        app,
        ["comment-update", "PROJ-1", "12345", "Replacement body"],
    )
    delete_result = runner.invoke(
        app,
        ["comment-delete", "PROJ-1", "12345", "--json"],
    )

    assert update_result.exit_code == 0
    assert update_result.stdout == "comment updated\n"
    assert delete_result.exit_code == 0
    assert delete_result.stdout == (
        '{\n  "comment_id": "12345",\n  "issue_key": "PROJ-1"\n}\n'
    )
    assert calls == [
        ("get_api", None),
        ("update", ("PROJ-1", "12345", "Replacement body")),
        ("get_api", None),
        ("delete", ("PROJ-1", "12345")),
    ]


def test_attachment_flat_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.attachments",
        attachments={
            "list": lambda issue_key: (
                calls.append(("list", issue_key))
                or HelperResult.text_only("attachment list")
            ),
            "read": lambda attachment_id: (
                calls.append(("read", attachment_id))
                or HelperResult.text_only("attachment metadata")
            ),
            "download": lambda attachment_id, *, output_path: (
                calls.append(("download", (attachment_id, output_path)))
                or HelperResult.with_data(
                    "ignored",
                    {"attachment_id": attachment_id, "output_path": output_path},
                )
            ),
            "upload": lambda issue_key, path: (
                calls.append(("upload", (issue_key, path)))
                or HelperResult.text_only("attachment uploaded")
            ),
            "delete": lambda attachment_id: (
                calls.append(("delete", attachment_id))
                or HelperResult.with_data("ignored", {"attachment_id": attachment_id})
            ),
        },
    )

    list_result = runner.invoke(app, ["attachment-list", "PROJ-1"])
    read_result = runner.invoke(app, ["attachment-read", "63899"])
    download_result = runner.invoke(
        app,
        ["attachment-download", "63899", "--output-path", "downloads/", "--raw"],
    )
    upload_result = runner.invoke(
        app,
        ["attachment-upload", "PROJ-1", "notes.txt"],
    )
    delete_result = runner.invoke(app, ["attachment-delete", "63899", "--json"])

    assert list_result.exit_code == 0
    assert list_result.stdout == "attachment list\n"
    assert read_result.exit_code == 0
    assert read_result.stdout == "attachment metadata\n"
    assert download_result.exit_code == 0
    assert download_result.stdout == (
        '{\n  "attachment_id": "63899",\n  "output_path": "downloads/"\n}\n'
    )
    assert upload_result.exit_code == 0
    assert upload_result.stdout == "attachment uploaded\n"
    assert delete_result.exit_code == 0
    assert delete_result.stdout == '{\n  "attachment_id": "63899"\n}\n'
    assert calls == [
        ("get_api", None),
        ("list", "PROJ-1"),
        ("get_api", None),
        ("read", "63899"),
        ("get_api", None),
        ("download", ("63899", "downloads/")),
        ("get_api", None),
        ("upload", ("PROJ-1", "notes.txt")),
        ("get_api", None),
        ("delete", "63899"),
    ]


def test_issue_links_command_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.links",
        links={
            "list": lambda issue_key: (
                calls.append(("list", issue_key))
                or HelperResult.with_data("ignored", {"issue_key": issue_key})
            )
        },
    )

    result = runner.invoke(app, ["issue-links", "PROJ-1", "--raw"])

    assert result.exit_code == 0
    assert result.stdout == '{\n  "issue_key": "PROJ-1"\n}\n'
    assert calls == [("get_api", None), ("list", "PROJ-1")]


def test_worklog_flat_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.worklogs",
        worklogs={
            "list": lambda issue_key, *, start_at, max_results: (
                calls.append(("list", (issue_key, start_at, max_results)))
                or HelperResult.with_data("ignored", {"issue_key": issue_key})
            ),
            "add": lambda issue_key, time_spent, *, started, comment: (
                calls.append(("add", (issue_key, time_spent, started, comment)))
                or HelperResult.text_only("worklog added")
            ),
            "update": lambda issue_key, worklog_id, *, time_spent, started, comment: (
                calls.append(
                    (
                        "update",
                        (issue_key, worklog_id, time_spent, started, comment),
                    )
                )
                or HelperResult.text_only("worklog updated")
            ),
            "delete": lambda issue_key, worklog_id: (
                calls.append(("delete", (issue_key, worklog_id)))
                or HelperResult.with_data("ignored", {"worklog_id": worklog_id})
            ),
        },
    )

    list_result = runner.invoke(
        app,
        ["worklogs", "PROJ-1", "--start-at", "2", "--max-results", "3", "--json"],
    )
    add_result = runner.invoke(
        app,
        [
            "worklog-add",
            "PROJ-1",
            "1h 30m",
            "--started",
            "2026-06-27T09:00:00.000+0000",
            "--comment",
            "Worked on it",
        ],
    )
    update_result = runner.invoke(
        app,
        ["worklog-update", "PROJ-1", "wl-1", "--time-spent", "45m"],
    )
    delete_result = runner.invoke(
        app,
        ["worklog-delete", "PROJ-1", "wl-1", "--raw"],
    )

    assert list_result.exit_code == 0
    assert list_result.stdout == '{\n  "issue_key": "PROJ-1"\n}\n'
    assert add_result.exit_code == 0
    assert add_result.stdout == "worklog added\n"
    assert update_result.exit_code == 0
    assert update_result.stdout == "worklog updated\n"
    assert delete_result.exit_code == 0
    assert delete_result.stdout == '{\n  "worklog_id": "wl-1"\n}\n'
    assert calls == [
        ("get_api", None),
        ("list", ("PROJ-1", 2, 3)),
        ("get_api", None),
        (
            "add",
            (
                "PROJ-1",
                "1h 30m",
                "2026-06-27T09:00:00.000+0000",
                "Worked on it",
            ),
        ),
        ("get_api", None),
        ("update", ("PROJ-1", "wl-1", "45m", None, None)),
        ("get_api", None),
        ("delete", ("PROJ-1", "wl-1")),
    ]


def test_project_status_priority_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.metadata",
        metadata={
            "project": lambda project_id_or_key: (
                calls.append(("project", project_id_or_key))
                or HelperResult.text_only("project details")
            ),
            "statuses": lambda: (
                calls.append(("statuses", None))
                or HelperResult.with_data("ignored", {"statuses": ["Open"]})
            ),
            "priorities": lambda: (
                calls.append(("priorities", None))
                or HelperResult.text_only("priority list")
            ),
        },
    )

    project_result = runner.invoke(app, ["project", "PROJ"])
    statuses_result = runner.invoke(app, ["statuses", "--json"])
    priorities_result = runner.invoke(app, ["priorities"])

    assert project_result.exit_code == 0
    assert project_result.stdout == "project details\n"
    assert statuses_result.exit_code == 0
    assert statuses_result.stdout == '{\n  "statuses": [\n    "Open"\n  ]\n}\n'
    assert priorities_result.exit_code == 0
    assert priorities_result.stdout == "priority list\n"
    assert calls == [
        ("get_api", None),
        ("project", "PROJ"),
        ("get_api", None),
        ("statuses", None),
        ("get_api", None),
        ("priorities", None),
    ]


def test_filters_commands_delegate_to_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.filters",
        filters={
            "list": lambda *, start_at, max_results: (
                calls.append(("list", (start_at, max_results)))
                or HelperResult.text_only("filter list")
            ),
            "search": lambda query, *, start_at, max_results: (
                calls.append(("search", (query, start_at, max_results)))
                or HelperResult.text_only("filter search")
            ),
            "run": lambda filter_id, *, max_results, fields: (
                calls.append(("run", (filter_id, max_results, fields)))
                or HelperResult.with_data(
                    "ignored",
                    {"filter_id": filter_id, "fields": fields},
                )
            ),
        },
    )

    list_result = runner.invoke(
        app, ["filters", "--start-at", "1", "--max-results", "2"]
    )
    search_result = runner.invoke(
        app,
        ["filters", "--query", "mine", "--start-at", "3", "--max-results", "4"],
    )
    run_result = runner.invoke(
        app,
        [
            "filter-run",
            "10400",
            "--max-results",
            "5",
            "--field",
            "summary",
            "--field",
            "status",
            "--raw",
        ],
    )

    assert list_result.exit_code == 0
    assert list_result.stdout == "filter list\n"
    assert search_result.exit_code == 0
    assert search_result.stdout == "filter search\n"
    assert run_result.exit_code == 0
    assert run_result.stdout == (
        "{\n"
        '  "fields": [\n'
        '    "summary",\n'
        '    "status"\n'
        "  ],\n"
        '  "filter_id": "10400"\n'
        "}\n"
    )
    assert calls == [
        ("get_api", None),
        ("list", (1, 2)),
        ("get_api", None),
        ("search", ("mine", 3, 4)),
        ("get_api", None),
        ("run", ("10400", 5, ["summary", "status"])),
    ]


def test_new_commands_are_flat_root_commands() -> None:
    root_command_names = set(
        _get_registered_command(name).name
        for name in [
            "auth-status",
            "attachment-upload",
            "comment-update",
            "filter-run",
            "issue-links",
            "me",
            "priorities",
            "project",
            "statuses",
            "transition",
            "transitions",
            "worklog-add",
        ]
    )

    assert root_command_names == {
        "auth-status",
        "attachment-upload",
        "comment-update",
        "filter-run",
        "issue-links",
        "me",
        "priorities",
        "project",
        "statuses",
        "transition",
        "transitions",
        "worklog-add",
    }
