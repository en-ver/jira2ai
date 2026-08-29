from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, cast

import pytest
from click.utils import strip_ansi
from jira2cli import app
from jira2cli.commands.changelogs import changelogs_by_ids_command
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()


def _patch_helpers(monkeypatch: pytest.MonkeyPatch, **methods: object) -> None:
    monkeypatch.setattr(
        "jira2cli.commands.changelogs.JiraHelpers",
        lambda _api: SimpleNamespace(changelogs=SimpleNamespace(**methods)),
    )


def test_changelogs_command_delegates_complete_history_and_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    api = object()
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_list(issue_key: str, **kwargs: object) -> HelperResult:
        calls.append(("list", (issue_key, kwargs)))
        return HelperResult.text_only("formatted changelogs")

    _patch_helpers(monkeypatch, list=fake_list)

    result = runner.invoke(
        app,
        [
            "changelogs",
            "PROJ-123",
            "--created-at-or-after",
            "2026-08-01T00:00:00Z",
            "--created-before",
            "2026-09-01T00:00:00Z",
            "--field-ids",
            "summary,customfield_10001",
            "--result-start-at",
            "2",
            "--result-max-results",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "formatted changelogs\n"
    assert calls == [
        ("get_api", None),
        (
            "list",
            (
                "PROJ-123",
                {
                    "created_at_or_after": "2026-08-01T00:00:00Z",
                    "created_before": "2026-09-01T00:00:00Z",
                    "field_ids": ["summary", "customfield_10001"],
                    "result_start_at": 2,
                    "result_max_results": 3,
                },
            ),
        ),
    ]


def test_changelogs_by_ids_parses_csv_preserves_order_and_renders_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())

    def fake_list_by_ids(
        issue_key: str,
        changelog_ids: list[int],
        *,
        field_ids: list[str] | None,
    ) -> HelperResult:
        calls.append((issue_key, changelog_ids, field_ids))
        return HelperResult.with_data(
            "formatted changelogs",
            {"issue_key": issue_key, "changelogs": [{"id": "10001"}]},
        )

    _patch_helpers(monkeypatch, list_by_ids=fake_list_by_ids)

    result = runner.invoke(
        app,
        [
            "changelogs-by-ids",
            "PROJ-123",
            "--changelog-ids",
            "10001, 10002,10001",
            "--field-ids",
            "summary, customfield_10001",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "issue_key": "PROJ-123",
        "changelogs": [{"id": "10001"}],
    }
    assert calls == [
        ("PROJ-123", [10001, 10002, 10001], ["summary", "customfield_10001"])
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["changelogs-by-ids", "PROJ-123"],
        [
            "changelogs-by-ids",
            "PROJ-123",
            "--changelog-ids",
            "10001",
            "--changelog-ids",
            "10002",
        ],
        ["changelogs-by-ids", "PROJ-123", "--changelog-ids", ""],
        ["changelogs-by-ids", "PROJ-123", "--changelog-ids", "10001,,10002"],
        ["changelogs-by-ids", "PROJ-123", "--changelog-ids", "10001.5"],
        ["changelogs-by-ids", "PROJ-123", "--changelog-ids", "[10001]"],
        ["changelogs-by-ids", "PROJ-123", "--changelog-ids", "abc"],
    ],
)
def test_changelogs_by_ids_rejects_invalid_csv_before_api(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, argv)

    assert result.exit_code == 2
    assert result.stdout == ""


def test_changelogs_by_ids_rejects_conflicting_output_modes_before_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(
        app,
        [
            "changelogs-by-ids",
            "PROJ-123",
            "--changelog-ids",
            "10001",
            "--json",
            "--raw",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Use only one of --json or --raw." in result.stderr


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (JiraHelperValidationError("invalid history input"), 2),
        (JiraHelperOperationError("history request failed"), 1),
    ],
)
def test_changelog_commands_use_cli_error_mapping(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_code: int,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        list=lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )

    result = runner.invoke(app, ["changelogs", "PROJ-123"])

    assert result.exit_code == expected_code
    assert result.stdout == ""
    assert result.stderr == f"{error}\n"


def test_changelog_command_help_and_registration_match_contract() -> None:
    root_help = runner.invoke(app, ["--help"])
    by_ids_help = runner.invoke(app, ["changelogs-by-ids", "--help"])
    history_help = runner.invoke(app, ["changelogs", "--help"])
    by_ids_command = cast(Any, get_command(app)).commands["changelogs-by-ids"]

    assert root_help.exit_code == 0
    assert "changelogs" in root_help.stdout
    assert "changelogs-by-ids" in root_help.stdout
    assert by_ids_help.exit_code == 0
    assert history_help.exit_code == 0

    command_help = " ".join(strip_ansi(by_ids_help.stdout).replace("│", " ").split())
    assert "--changelog-ids" in command_help
    assert "Required exactly once" in command_help
    assert "--changelog-id " not in command_help
    assert "--field-ids" in command_help
    assert "--result-start-at" not in command_help
    history_command_help = " ".join(
        strip_ansi(history_help.stdout).replace("│", " ").split()
    )
    assert "complete changelog history" in history_command_help.lower()
    assert "--field-ids" in history_command_help
    assert "--result-start-at" in history_command_help
    assert "--result-max-results" in history_command_help

    assert [param.name for param in by_ids_command.params] == [
        "issue_key",
        "changelog_ids",
        "field_ids",
        "raw_output",
        "json_output",
    ]
    assert [param.opts for param in by_ids_command.params] == [
        ["issue_key"],
        ["--changelog-ids"],
        ["--field-ids"],
        ["--raw"],
        ["--json"],
    ]
    assert by_ids_command.params[1].required is True
    assert list(changelogs_by_ids_command.__annotations__)[:2] == [
        "issue_key",
        "changelog_ids",
    ]
