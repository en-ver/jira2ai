from __future__ import annotations

import inspect
import json
from textwrap import dedent
from types import SimpleNamespace
from typing import Any, cast

import pytest
from jira2cli import app
from jira2cli.commands.worklogs import worklog_report_command
from jira2cli.jql import JQL_REFERENCE
from jira2py import JiraError
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import (
    AttachmentDownloadError,
    JiraHelperValidationError,
)
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()

FIELD_SELECTION_HELP = (
    "Comma-separated Jira field keys, IDs, or selectors. Provide --fields "
    "at most once. If omitted, fields default to summary, status, assignee, "
    "priority, issuetype, created, updated. Projection is whole-field: "
    "assignee may include Jira-permitted nested identity, email, and avatar "
    "data; envelope metadata may remain."
)
RAW_OUTPUT_HELP = (
    "Render API-oriented output as normalized, pretty-printed JSON with sorted "
    "object keys."
)


def _get_registered_command(command_name: str):
    return cast(Any, get_command(app)).commands[command_name]


def _patch_helpers(monkeypatch: pytest.MonkeyPatch, module_path: str, **groups) -> None:
    monkeypatch.setattr(
        f"{module_path}.JiraHelpers",
        lambda _api: SimpleNamespace(
            **{name: SimpleNamespace(**methods) for name, methods in groups.items()}
        ),
    )


def test_search_field_help_explains_field_level_selection() -> None:
    command = _get_registered_command("search")
    fields = next(param for param in command.params if param.name == "fields")

    assert fields.help == FIELD_SELECTION_HELP


def test_all_raw_output_options_describe_normalized_json() -> None:
    raw_output_options = [
        param
        for command in get_command(app).commands.values()
        for param in command.params
        if param.name == "raw_output"
    ]

    assert raw_output_options
    assert all(option.help == RAW_OUTPUT_HELP for option in raw_output_options)


def test_root_help_lists_registered_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command_name in [
        "read",
        "search",
        "worklog-report",
        "comments",
        "fields",
        "projects",
        "users",
        "link-types",
        "jql-syntax",
        "create",
        "edit",
        "comment",
        "add-link",
        "delete-link",
        "attachment",
    ]:
        assert command_name in result.stdout


def test_read_command_normalizes_padded_issue_key_before_api_and_formats_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    data = {"key": "PROJ-123", "fields": {"summary": "Formatted issue"}}

    def fake_get_issue(*, issue_id: str, fields: list[str]) -> dict[str, object]:
        calls.append(("get_issue", (issue_id, fields)))
        return data

    api = SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        issues=SimpleNamespace(get_issue=fake_get_issue),
    )
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_format_issue(
        received_data: dict[str, object],
        *,
        browse_url: str,
    ) -> str:
        calls.append(("format_issue", (received_data, browse_url)))
        return "formatted issue"

    monkeypatch.setattr("jira2cli.commands.read.format_issue", fake_format_issue)

    result = runner.invoke(
        app,
        ["read", "  PROJ-123  ", "--fields", "summary, customfield_10001"],
    )

    assert result.exit_code == 0
    assert result.stdout == "formatted issue\n"
    assert calls == [
        ("get_api", None),
        ("get_issue", ("PROJ-123", ["summary", "customfield_10001"])),
        (
            "format_issue",
            (
                data,
                "https://example.atlassian.net/browse/PROJ-123",
            ),
        ),
    ]


def test_read_command_json_bypasses_formatter_and_browse_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = {
        "key": "PROJ-123",
        "fields": {
            "description": {"type": "doc", "version": 1, "content": []},
            "summary": "Unformatted",
        },
    }
    calls: list[dict[str, object]] = []

    def fake_get_issue(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return data

    api = SimpleNamespace(issues=SimpleNamespace(get_issue=fake_get_issue))
    monkeypatch.setattr("jira2cli.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2cli.commands.read.format_issue",
        lambda *_args, **_kwargs: pytest.fail("formatter must not be called"),
    )

    result = runner.invoke(
        app,
        ["read", "PROJ-123", "--fields", "description,summary", "--json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == data
    assert calls == [
        {
            "issue_id": "PROJ-123",
            "fields": ["description", "summary"],
        }
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["read", "PROJ-123"],
        ["read", "PROJ-123", "--fields", "summary", "--fields", "status"],
        ["read", "PROJ-123", "--fields", "summary,,status"],
        ["read", "PROJ-123", "--fields", "summary", "--raw"],
        ["read", "PROJ-123", "--fields", "summary", "--extra-field", "labels"],
    ],
)
def test_read_command_rejects_invalid_or_removed_options_before_api(
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


def test_read_command_rejects_blank_issue_key_before_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["read", "   ", "--fields", "summary"])

    assert result.exit_code == 2
    assert result.stdout == ""


def test_read_command_preserves_jira_error_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = SimpleNamespace(
        issues=SimpleNamespace(
            get_issue=lambda **_kwargs: (_ for _ in ()).throw(JiraError("boom"))
        )
    )
    monkeypatch.setattr("jira2cli.client.get_api", lambda: api)

    result = runner.invoke(app, ["read", "  PROJ-404  ", "--fields", "summary"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Failed to fetch issue PROJ-404: boom\n"


def test_read_command_surfaces_formatter_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        issues=SimpleNamespace(
            get_issue=lambda **_kwargs: {"key": "PROJ-123", "fields": {}}
        ),
    )
    monkeypatch.setattr("jira2cli.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2cli.commands.read.format_issue",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("format failed")),
    )

    result = runner.invoke(app, ["read", "PROJ-123", "--fields", "summary"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "format failed\n"


def test_read_help_requires_fields_and_omits_legacy_options() -> None:
    result = runner.invoke(app, ["read", "--help"])

    assert result.exit_code == 0
    assert "--fields" in result.stdout
    assert "[required]" in result.stdout
    assert "--extra-field" not in result.stdout
    assert "--raw" not in result.stdout


def test_search_command_manually_continues_with_an_opaque_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    token = "opaque token /?=+"

    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())

    def fake_issues(jql: str, **kwargs: object) -> HelperResult:
        calls.append((jql, kwargs))
        return HelperResult.with_data(
            "ignored",
            {
                "issues": [],
                "nextPageToken": token if len(calls) == 1 else None,
            },
        )

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.search",
        search={"issues": fake_issues},
    )

    argv = [
        "search",
        "project = PROJ ORDER BY created DESC",
        "--max-results",
        "7",
        "--fields",
        "summary,status",
        "--json",
    ]
    first_result = runner.invoke(app, argv)
    second_result = runner.invoke(app, [*argv, "--next-page-token", token])

    assert first_result.exit_code == 0
    assert json.loads(first_result.stdout)["nextPageToken"] == token
    assert second_result.exit_code == 0
    assert json.loads(second_result.stdout)["nextPageToken"] is None
    assert calls == [
        (
            "project = PROJ ORDER BY created DESC",
            {"max_results": 7, "fields": ["summary", "status"]},
        ),
        (
            "project = PROJ ORDER BY created DESC",
            {
                "max_results": 7,
                "fields": ["summary", "status"],
                "next_page_token": token,
            },
        ),
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["search", "project = PROJ", "--fields", "summary", "--fields", "status"],
        ["filter-run", "10400", "--fields", "summary", "--fields", "status"],
    ],
)
def test_search_and_filter_run_reject_repeated_fields_before_api(
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
    assert result.stderr == "--fields: may be provided only once\n"


def test_search_omits_fields_to_preserve_helper_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.search",
        search={
            "issues": lambda _jql, **kwargs: (
                calls.append(kwargs) or HelperResult.text_only("search result")
            )
        },
    )

    result = runner.invoke(app, ["search", "project = PROJ"])

    assert result.exit_code == 0
    assert calls == [{"max_results": 20, "fields": None}]


def test_filter_run_omits_fields_to_preserve_helper_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.filters",
        filters={
            "run": lambda _filter_id, **kwargs: (
                calls.append(kwargs) or HelperResult.text_only("filter result")
            )
        },
    )

    result = runner.invoke(app, ["filter-run", "10400"])

    assert result.exit_code == 0
    assert calls == [{"max_results": 20, "fields": None}]


def test_worklog_report_command_help_is_jql_only() -> None:
    result = runner.invoke(app, ["worklog-report", "--help"])
    command = _get_registered_command("worklog-report")

    assert result.exit_code == 0
    assert command.help == "Build a Jira worklog report for JQL-selected issues."
    assert [param.name for param in command.params] == [
        "start_date",
        "end_date",
        "jql",
        "account_id",
        "max_issues",
        "include_details",
        "raw_output",
        "json_output",
    ]
    assert [param.opts for param in command.params] == [
        ["--start-date"],
        ["--end-date"],
        ["--jql"],
        ["--account-id"],
        ["--max-issues"],
        ["--include-details"],
        ["--raw"],
        ["--json"],
    ]
    assert {param.opts[0] for param in command.params if param.required} == {
        "--start-date",
        "--end-date",
        "--jql",
    }

    registered_options = {option for param in command.params for option in param.opts}
    forbidden_options = {
        "--issue",
        "--issue-id",
        "--issue-key",
        "--issue-id-or-key",
        "--task",
        "--task-id",
        "--task-key",
    }
    assert forbidden_options.isdisjoint(registered_options)


def test_worklog_report_command_signature_is_jql_only() -> None:
    parameter_names = list(inspect.signature(worklog_report_command).parameters)

    assert parameter_names == [
        "start_date",
        "end_date",
        "jql",
        "account_id",
        "max_issues",
        "include_details",
        "raw_output",
        "json_output",
    ]
    forbidden = {
        "issue",
        "issue_id",
        "issue_key",
        "issue_id_or_key",
        "task",
        "task_id",
        "task_key",
    }
    assert forbidden.isdisjoint(parameter_names)


def test_worklog_report_command_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )

    def fake_report(
        *,
        start_date: str,
        end_date: str,
        jql: str,
        account_id: str | None = None,
        max_issues: int = 100,
        include_details: bool = False,
    ):
        calls.append(
            (
                "report",
                (
                    start_date,
                    end_date,
                    jql,
                    account_id,
                    max_issues,
                    include_details,
                ),
            )
        )
        return HelperResult.text_only("formatted worklog report")

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.worklogs",
        worklogs={"report": fake_report},
    )

    result = runner.invoke(
        app,
        [
            "worklog-report",
            "--start-date",
            "2026-06-12",
            "--end-date",
            "2026-06-13",
            "--jql",
            "project = PROJ",
            "--account-id",
            "acct-1",
            "--max-issues",
            "25",
            "--include-details",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "formatted worklog report\n"
    assert calls == [
        ("get_api", None),
        (
            "report",
            ("2026-06-12", "2026-06-13", "project = PROJ", "acct-1", 25, True),
        ),
    ]


def test_worklog_report_command_json_output_uses_structured_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.worklogs",
        worklogs={
            "report": lambda **kwargs: HelperResult.with_data(
                "ignored",
                {**kwargs, "api_matches": True},
            )
        },
    )

    result = runner.invoke(
        app,
        [
            "worklog-report",
            "--start-date",
            "2026-06-12",
            "--end-date",
            "2026-06-13",
            "--jql",
            "project = PROJ",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "{\n"
        '  "account_id": null,\n'
        '  "api_matches": true,\n'
        '  "end_date": "2026-06-13",\n'
        '  "include_details": false,\n'
        '  "jql": "project = PROJ",\n'
        '  "max_issues": 100,\n'
        '  "start_date": "2026-06-12"\n'
        "}\n"
    )


def test_worklog_report_command_raw_output_uses_structured_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.worklogs",
        worklogs={
            "report": lambda **_: HelperResult.with_data(
                "ignored",
                {
                    "rowCount": 1,
                    "rows": [{"issueKey": "PROJ-1"}],
                },
            )
        },
    )

    result = runner.invoke(
        app,
        [
            "worklog-report",
            "--start-date",
            "2026-06-12",
            "--end-date",
            "2026-06-13",
            "--jql",
            "project = PROJ",
            "--raw",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "{\n"
        '  "rowCount": 1,\n'
        '  "rows": [\n'
        "    {\n"
        '      "issueKey": "PROJ-1"\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def test_worklog_report_command_preserves_formatted_multi_row_details_and_truncation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formatted_report = dedent(
        """\
        Worklog report
        Date range: 2026-06-12 to 2026-06-13 (UTC; end date inclusive)
        Account: acct-1
        JQL: project = PROJ
        Issues scanned: 2 (max 2, truncated)
        Rows: 2
        Total: 1.50h (5400s)
        Issue search total: 5
        More issues matched the JQL but were not scanned.

        --- [ROWS (2)] ---
        - 2026-06-12T09:30:00Z — PROJ-1 — Alice (acct-1) — 1.00h
          issueId: 10001 | project: PROJ | summary: First task | worklogId: wl-1
          timeSpent: 1h / 3600s
          started: 2026-06-12T09:30:00Z
          created: 2026-06-12T09:35:00Z
          updated: 2026-06-12T09:40:00Z
          updateAuthor: Reviewer (acct-9)
          visibility: role / Developers
          comment: Finished the implementation
        - 2026-06-13T10:15:00Z — PROJ-2 — Bob (acct-2) — 0.50h
          issueId: 10002 | project: PROJ | summary: Second task | worklogId: wl-2
          timeSpent: 30m / 1800s
          started: 2026-06-13T10:15:00Z
          created: 2026-06-13T10:20:00Z
          updated: 2026-06-13T10:25:00Z
        """
    ).strip()

    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.worklogs",
        worklogs={
            "report": lambda **_: HelperResult.text_only(formatted_report),
        },
    )

    result = runner.invoke(
        app,
        [
            "worklog-report",
            "--start-date",
            "2026-06-12",
            "--end-date",
            "2026-06-13",
            "--jql",
            "project = PROJ",
            "--account-id",
            "acct-1",
            "--max-issues",
            "2",
            "--include-details",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == f"{formatted_report}\n"


def test_comments_command_raw_output_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.read",
        comments={
            "list": lambda issue_key, *, start_at, max_results, order_by: (
                HelperResult.with_data(
                    "ignored",
                    {
                        "issue_key": issue_key,
                        "start_at": start_at,
                        "max_results": max_results,
                        "order_by": order_by,
                    },
                )
            )
        },
    )

    result = runner.invoke(
        app,
        [
            "comments",
            "PROJ-123",
            "--start-at",
            "2",
            "--max-results",
            "3",
            "--order-by",
            "-created",
            "--raw",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "{\n"
        '  "issue_key": "PROJ-123",\n'
        '  "max_results": 3,\n'
        '  "order_by": "-created",\n'
        '  "start_at": 2\n'
        "}\n"
    )


def test_fields_command_issue_key_takes_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )

    def fake_edit_fields(issue_key: str):
        calls.append(("edit_fields", issue_key))
        return HelperResult.text_only("edit fields")

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.metadata",
        metadata={
            "edit_fields": fake_edit_fields,
            "issue_types": lambda _project_key: pytest.fail(
                "should not list issue types"
            ),
            "create_fields": lambda _project_key, _issue_type: pytest.fail(
                "should not get create fields"
            ),
        },
    )

    result = runner.invoke(
        app,
        [
            "fields",
            "--issue-key",
            "PROJ-123",
            "--project-key",
            "PROJ",
            "--issue-type",
            "Bug",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "edit fields\n"
    assert calls == [
        ("get_api", None),
        ("edit_fields", "PROJ-123"),
    ]


@pytest.mark.parametrize(
    ("argv", "patched_attr", "expected_text"),
    [
        (
            ["fields", "--project-key", "PROJ"],
            "issue_types",
            "issue types",
        ),
        (
            ["fields", "--project-key", "PROJ", "--issue-type", "Bug"],
            "create_fields",
            "create fields",
        ),
    ],
)
def test_fields_command_project_modes(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    patched_attr: str,
    expected_text: str,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())

    metadata_methods = {
        "edit_fields": lambda _issue_key: pytest.fail("should not get edit fields"),
        "issue_types": lambda project_key: HelperResult.text_only(expected_text),
        "create_fields": lambda project_key, issue_type: HelperResult.text_only(
            expected_text
        ),
    }
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.metadata",
        metadata=metadata_methods,
    )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == f"{expected_text}\n"


def test_fields_command_requires_project_or_issue_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["fields"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "Provide either --project-key (to list issue types / create fields) or --issue-key (to list edit fields).\n"
    )


@pytest.mark.parametrize(
    ("command_name", "module_path", "argv", "expected_text"),
    [
        (
            "projects",
            "jira2cli.commands.metadata",
            ["projects", "--query", "ops"],
            "projects result",
        ),
        (
            "users",
            "jira2cli.commands.metadata",
            ["users", "alice", "--max-results", "5"],
            "users result",
        ),
        (
            "link-types",
            "jira2cli.commands.metadata",
            ["link-types"],
            "link types result",
        ),
    ],
)
def test_metadata_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
    command_name: str,
    module_path: str,
    argv: list[str],
    expected_text: str,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())

    if command_name == "projects":
        metadata = {"projects": lambda query: HelperResult.text_only(expected_text)}
        _patch_helpers(monkeypatch, module_path, metadata=metadata)
    elif command_name == "users":
        metadata = {
            "users": lambda query, *, max_results: HelperResult.text_only(expected_text)
        }
        _patch_helpers(monkeypatch, module_path, metadata=metadata)
    else:
        _patch_helpers(
            monkeypatch,
            module_path,
            links={"types": lambda: HelperResult.text_only(expected_text)},
        )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == f"{expected_text}\n"


def test_jql_syntax_command_prints_shared_reference_without_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["jql-syntax"])

    assert result.exit_code == 0
    assert result.stdout == f"{JQL_REFERENCE}\n"


def test_create_command_parses_fields_json_and_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )

    def fake_create(
        project_key: str,
        issue_type: str,
        summary: str,
        *,
        description,
        fields,
    ):
        calls.append(
            (
                "create",
                (project_key, issue_type, summary, description, fields),
            )
        )
        return HelperResult.text_only("created")

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.write",
        issues={"create": fake_create},
    )

    result = runner.invoke(
        app,
        [
            "create",
            "PROJ",
            "Bug",
            "Broken build",
            "--description",
            "Fix this",
            "--fields-json",
            '{"priority": {"name": "High"}}',
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "created\n"
    assert calls == [
        ("get_api", None),
        (
            "create",
            (
                "PROJ",
                "Bug",
                "Broken build",
                "Fix this",
                {"priority": {"name": "High"}},
            ),
        ),
    ]


def test_edit_command_json_output_requests_raw_helper_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )

    def fake_edit(
        issue_key: str,
        *,
        summary,
        description,
        fields,
        raw,
    ):
        calls.append(
            (
                "edit",
                (issue_key, summary, description, fields, raw),
            )
        )
        return HelperResult.with_data(
            "updated",
            {"issue_key": issue_key, "summary": summary, "fields": fields},
        )

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.write",
        issues={"edit": fake_edit},
    )

    result = runner.invoke(
        app,
        [
            "edit",
            "PROJ-123",
            "--summary",
            "Updated summary",
            "--fields-json",
            '{"priority": {"name": "Low"}}',
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "{\n"
        '  "fields": {\n'
        '    "priority": {\n'
        '      "name": "Low"\n'
        "    }\n"
        "  },\n"
        '  "issue_key": "PROJ-123",\n'
        '  "summary": "Updated summary"\n'
        "}\n"
    )
    assert calls == [
        ("get_api", None),
        (
            "edit",
            (
                "PROJ-123",
                "Updated summary",
                None,
                {"priority": {"name": "Low"}},
                True,
            ),
        ),
    ]


def test_comment_command_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )

    def fake_add(issue_key: str, body: str):
        calls.append(("add", (issue_key, body)))
        return HelperResult.text_only("comment added")

    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.write",
        comments={"add": fake_add},
    )

    result = runner.invoke(app, ["comment", "PROJ-123", "Ship it"])

    assert result.exit_code == 0
    assert result.stdout == "comment added\n"
    assert calls == [
        ("get_api", None),
        ("add", ("PROJ-123", "Ship it")),
    ]


@pytest.mark.parametrize(
    ("argv", "group_name", "method_name", "expected_stdout"),
    [
        (
            ["add-link", "Blocks", "PROJ-1", "PROJ-2", "--raw"],
            "links",
            "create",
            "{\n"
            '  "inward_issue": "PROJ-2",\n'
            '  "link_type": "Blocks",\n'
            '  "outward_issue": "PROJ-1"\n'
            "}\n",
        ),
        (
            ["delete-link", "12345"],
            "links",
            "delete",
            "link deleted\n",
        ),
    ],
)
def test_link_commands_delegate_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    group_name: str,
    method_name: str,
    expected_stdout: str,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())

    if method_name == "create":
        _patch_helpers(
            monkeypatch,
            "jira2cli.commands.links",
            links={
                "create": lambda link_type, outward_key, inward_key: (
                    HelperResult.with_data(
                        "ignored",
                        {
                            "link_type": link_type,
                            "outward_issue": outward_key,
                            "inward_issue": inward_key,
                        },
                    )
                )
            },
        )
    else:
        _patch_helpers(
            monkeypatch,
            "jira2cli.commands.links",
            links={"delete": lambda link_id: HelperResult.text_only("link deleted")},
        )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == expected_stdout


def test_attachment_command_delegates_to_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = SimpleNamespace(output_file="/tmp/debug.log")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: calls.append(("get_api", None)) or object(),
    )
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.attachments",
        attachments={
            "validate_id": lambda attachment_id: calls.append(
                ("validate_id", attachment_id)
            ),
            "plan_download": lambda attachment_id, *, output_path: (
                calls.append(("plan_download", (attachment_id, output_path)))
                or HelperResult.with_data("ignored", plan)
            ),
        },
    )
    monkeypatch.setattr(
        "jira2cli.commands.attachments.download_attachment_content",
        lambda received_plan, *, api: calls.append(("download", received_plan)),
    )
    monkeypatch.setattr(
        "jira2cli.commands.attachments.format_attachment_download_result",
        lambda received_plan: calls.append(("format", received_plan)) or "downloaded",
    )

    result = runner.invoke(
        app,
        ["attachment", "63899", "--output-path", "downloads/"],
    )

    assert result.exit_code == 0
    assert result.stdout == "downloaded\n"
    assert calls == [
        ("get_api", None),
        ("validate_id", "63899"),
        ("plan_download", ("63899", "downloads/")),
        ("download", plan),
        ("format", plan),
    ]


def test_attachment_command_rejects_empty_ids_before_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.attachments",
        attachments={
            "validate_id": lambda _attachment_id: (_ for _ in ()).throw(
                JiraHelperValidationError(
                    "attachment_id is required and cannot be empty"
                )
            )
        },
    )

    result = runner.invoke(app, ["attachment", "   "])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == "attachment_id is required and cannot be empty\n"


def test_attachment_command_reports_download_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = SimpleNamespace(output_file="/tmp/debug.log")

    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(
        monkeypatch,
        "jira2cli.commands.attachments",
        attachments={
            "validate_id": lambda _attachment_id: None,
            "plan_download": lambda attachment_id, *, output_path: (
                HelperResult.with_data("ignored", plan)
            ),
        },
    )
    monkeypatch.setattr(
        "jira2cli.commands.attachments.download_attachment_content",
        lambda _received_plan, *, api: (_ for _ in ()).throw(
            AttachmentDownloadError("download failed")
        ),
    )
    monkeypatch.setattr(
        "jira2cli.commands.attachments.format_attachment_download_result",
        lambda _received_plan: pytest.fail("format should not be called"),
    )

    result = runner.invoke(app, ["attachment", "63899"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "download failed\n"


def test_create_command_rejects_invalid_fields_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(
        app,
        [
            "create",
            "PROJ",
            "Bug",
            "Broken build",
            "--fields-json",
            "[1, 2, 3]",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "must be a JSON object" in result.stderr
    assert "--fields-json" in result.stderr


@pytest.mark.parametrize(
    ("argv", "module_path", "helpers_patch", "error", "expected_code"),
    [
        (
            ["projects"],
            "jira2cli.commands.metadata",
            {
                "metadata": {
                    "projects": lambda query: (_ for _ in ()).throw(
                        JiraHelperValidationError("bad input")
                    )
                }
            },
            JiraHelperValidationError("bad input"),
            2,
        ),
    ],
)
def test_commands_use_cli_friendly_error_handling(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    module_path: str,
    helpers_patch: dict[str, dict[str, object]],
    error: Exception,
    expected_code: int,
) -> None:
    monkeypatch.setattr("jira2cli.client.get_api", lambda: object())
    _patch_helpers(monkeypatch, module_path, **helpers_patch)

    result = runner.invoke(app, argv)

    assert result.exit_code == expected_code
    assert result.stdout == ""
    assert result.stderr == f"{error}\n"


def test_commands_reject_conflicting_output_modes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2cli.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(
        app,
        ["search", "project = PROJ", "--json", "--raw"],
    )

    assert result.exit_code == 2
    assert "Use only one of --json or --raw." in result.stderr
