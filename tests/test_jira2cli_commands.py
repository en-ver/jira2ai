from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest
from jira2ai_core.errors import (
    AttachmentDownloadError,
    Jira2AIValidationError,
    JiraOperationError,
)
from jira2ai_core.jql import JQL_REFERENCE
from jira2ai_core.results import OperationResult
from jira2cli import app
from jira2cli.commands.worklogs import worklog_report_command
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()


def _get_registered_command(command_name: str):
    return get_command(app).commands[command_name]


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


def test_read_command_delegates_to_core(monkeypatch: pytest.MonkeyPatch) -> None:
    api = SimpleNamespace(name="api")
    calls: list[tuple[str, object]] = []

    def fake_get_api():
        calls.append(("get_api", None))
        return api

    def fake_read_issue(issue_key: str, *, extra_fields, api):
        calls.append(("read_issue", (issue_key, extra_fields, api)))
        return OperationResult.text_only("formatted issue")

    monkeypatch.setattr("jira2ai_core.client.get_api", fake_get_api)
    monkeypatch.setattr("jira2ai_core.operations.issues.read_issue", fake_read_issue)

    result = runner.invoke(
        app,
        ["read", "PROJ-123", "--extra-field", "customfield_10001"],
    )

    assert result.exit_code == 0
    assert result.stdout == "formatted issue\n"
    assert calls == [
        ("get_api", None),
        ("read_issue", ("PROJ-123", ["customfield_10001"], api)),
    ]


def test_search_command_json_output_uses_structured_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.search.search_issues",
        lambda jql, *, max_results, fields, api: OperationResult.with_data(
            "ignored",
            {
                "jql": jql,
                "max_results": max_results,
                "fields": fields,
                "api_matches": api is not None,
            },
        ),
    )

    result = runner.invoke(
        app,
        [
            "search",
            "project = PROJ",
            "--max-results",
            "7",
            "--field",
            "summary",
            "--field",
            "status",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "{\n"
        '  "api_matches": true,\n'
        '  "fields": [\n'
        '    "summary",\n'
        '    "status"\n'
        "  ],\n"
        '  "jql": "project = PROJ",\n'
        '  "max_results": 7\n'
        "}\n"
    )


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


def test_worklog_report_command_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = SimpleNamespace(name="api")
    calls: list[tuple[str, object]] = []

    def fake_get_api():
        calls.append(("get_api", None))
        return api

    def fake_get_worklog_report(
        *,
        api,
        start_date: str,
        end_date: str,
        jql: str,
        account_id: str | None = None,
        max_issues: int = 100,
        include_details: bool = False,
    ):
        calls.append(
            (
                "get_worklog_report",
                (
                    api,
                    start_date,
                    end_date,
                    jql,
                    account_id,
                    max_issues,
                    include_details,
                ),
            )
        )
        return OperationResult.text_only("formatted worklog report")

    monkeypatch.setattr("jira2ai_core.client.get_api", fake_get_api)
    monkeypatch.setattr(
        "jira2ai_core.operations.worklogs.get_worklog_report",
        fake_get_worklog_report,
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
            "get_worklog_report",
            (api, "2026-06-12", "2026-06-13", "project = PROJ", "acct-1", 25, True),
        ),
    ]


def test_worklog_report_command_json_output_uses_structured_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.worklogs.get_worklog_report",
        lambda *, api, start_date, end_date, jql, account_id, max_issues, include_details: (
            OperationResult.with_data(
                "ignored",
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "jql": jql,
                    "account_id": account_id,
                    "max_issues": max_issues,
                    "include_details": include_details,
                    "api_matches": api is not None,
                },
            )
        ),
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
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.worklogs.get_worklog_report",
        lambda **_: OperationResult.with_data(
            "ignored",
            {
                "rowCount": 1,
                "rows": [{"issueKey": "PROJ-1"}],
            },
        ),
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


def test_comments_command_raw_output_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.comments.list_comments",
        lambda issue_key, *, start_at, max_results, order_by, api: (
            OperationResult.with_data(
                "ignored",
                {
                    "issue_key": issue_key,
                    "start_at": start_at,
                    "max_results": max_results,
                    "order_by": order_by,
                },
            )
        ),
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
    api = object()
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_get_edit_fields(issue_key: str, *, api):
        calls.append(("get_edit_fields", (issue_key, api)))
        return OperationResult.text_only("edit fields")

    monkeypatch.setattr(
        "jira2ai_core.operations.fields.get_edit_fields",
        fake_get_edit_fields,
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.fields.list_issue_types",
        lambda project_key, *, api: pytest.fail("should not list issue types"),
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.fields.get_create_fields",
        lambda project_key, issue_type, *, api: pytest.fail(
            "should not get create fields"
        ),
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
        ("get_edit_fields", ("PROJ-123", api)),
    ]


@pytest.mark.parametrize(
    ("argv", "patched_attr", "expected_text"),
    [
        (
            ["fields", "--project-key", "PROJ"],
            "list_issue_types",
            "issue types",
        ),
        (
            ["fields", "--project-key", "PROJ", "--issue-type", "Bug"],
            "get_create_fields",
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
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.fields.get_edit_fields",
        lambda issue_key, *, api: pytest.fail("should not get edit fields"),
    )

    monkeypatch.setattr(
        f"jira2ai_core.operations.fields.{patched_attr}",
        (
            (lambda project_key, *, api: OperationResult.text_only(expected_text))
            if patched_attr == "list_issue_types"
            else (
                lambda project_key, issue_type, *, api: OperationResult.text_only(
                    expected_text
                )
            )
        ),
    )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == f"{expected_text}\n"


def test_fields_command_requires_project_or_issue_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
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
    ("command_name", "operation_path", "argv", "expected_text"),
    [
        (
            "projects",
            "jira2ai_core.operations.projects.list_projects",
            ["projects", "--query", "ops"],
            "projects result",
        ),
        (
            "users",
            "jira2ai_core.operations.users.search_users",
            ["users", "alice", "--max-results", "5"],
            "users result",
        ),
        (
            "link-types",
            "jira2ai_core.operations.links.list_link_types",
            ["link-types"],
            "link types result",
        ),
    ],
)
def test_metadata_commands_delegate_to_core(
    monkeypatch: pytest.MonkeyPatch,
    command_name: str,
    operation_path: str,
    argv: list[str],
    expected_text: str,
) -> None:
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)

    if command_name == "projects":
        monkeypatch.setattr(
            operation_path,
            lambda query, *, api: OperationResult.text_only(expected_text),
        )
    elif command_name == "users":
        monkeypatch.setattr(
            operation_path,
            lambda query, *, max_results, api: OperationResult.text_only(expected_text),
        )
    else:
        monkeypatch.setattr(
            operation_path,
            lambda *, api: OperationResult.text_only(expected_text),
        )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == f"{expected_text}\n"


def test_jql_syntax_command_prints_shared_reference_without_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["jql-syntax"])

    assert result.exit_code == 0
    assert result.stdout == f"{JQL_REFERENCE}\n"


def test_create_command_parses_fields_json_and_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_create_issue(
        project_key: str,
        issue_type: str,
        summary: str,
        *,
        description,
        fields,
        api,
    ):
        calls.append(
            (
                "create_issue",
                (project_key, issue_type, summary, description, fields, api),
            )
        )
        return OperationResult.text_only("created")

    monkeypatch.setattr(
        "jira2ai_core.operations.issues.create_issue",
        fake_create_issue,
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
            "create_issue",
            (
                "PROJ",
                "Bug",
                "Broken build",
                "Fix this",
                {"priority": {"name": "High"}},
                api,
            ),
        ),
    ]


def test_edit_command_json_output_requests_raw_core_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_edit_issue(
        issue_key: str,
        *,
        summary,
        description,
        fields,
        raw,
        api,
    ):
        calls.append(
            (
                "edit_issue",
                (issue_key, summary, description, fields, raw, api),
            )
        )
        return OperationResult.with_data(
            "updated",
            {"issue_key": issue_key, "summary": summary, "fields": fields},
        )

    monkeypatch.setattr("jira2ai_core.operations.issues.edit_issue", fake_edit_issue)

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
            "edit_issue",
            (
                "PROJ-123",
                "Updated summary",
                None,
                {"priority": {"name": "Low"}},
                True,
                api,
            ),
        ),
    ]


def test_comment_command_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )

    def fake_add_comment(issue_key: str, body: str, *, api):
        calls.append(("add_comment", (issue_key, body, api)))
        return OperationResult.text_only("comment added")

    monkeypatch.setattr(
        "jira2ai_core.operations.comments.add_comment",
        fake_add_comment,
    )

    result = runner.invoke(app, ["comment", "PROJ-123", "Ship it"])

    assert result.exit_code == 0
    assert result.stdout == "comment added\n"
    assert calls == [
        ("get_api", None),
        ("add_comment", ("PROJ-123", "Ship it", api)),
    ]


@pytest.mark.parametrize(
    ("argv", "operation_path", "expected_stdout"),
    [
        (
            ["add-link", "Blocks", "PROJ-1", "PROJ-2", "--raw"],
            "jira2ai_core.operations.links.create_issue_link",
            "{\n"
            '  "inward_issue": "PROJ-2",\n'
            '  "link_type": "Blocks",\n'
            '  "outward_issue": "PROJ-1"\n'
            "}\n",
        ),
        (
            ["delete-link", "12345"],
            "jira2ai_core.operations.links.delete_issue_link",
            "link deleted\n",
        ),
    ],
)
def test_link_commands_delegate_to_core(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    operation_path: str,
    expected_stdout: str,
) -> None:
    api = object()

    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)

    if operation_path.endswith("create_issue_link"):
        monkeypatch.setattr(
            operation_path,
            lambda link_type, outward_key, inward_key, *, api: (
                OperationResult.with_data(
                    "ignored",
                    {
                        "link_type": link_type,
                        "outward_issue": outward_key,
                        "inward_issue": inward_key,
                    },
                )
            ),
        )
    else:
        monkeypatch.setattr(
            operation_path,
            lambda link_id, *, api: OperationResult.text_only("link deleted"),
        )

    result = runner.invoke(app, argv)

    assert result.exit_code == 0
    assert result.stdout == expected_stdout


def test_attachment_command_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()
    plan = SimpleNamespace(output_file="/tmp/debug.log")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.validate_attachment_id",
        lambda attachment_id: calls.append(("validate_attachment_id", attachment_id)),
    )
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: calls.append(("get_api", None)) or api,
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.plan_attachment_download",
        lambda attachment_id, *, output_path, api: (
            calls.append(
                (
                    "plan_attachment_download",
                    (attachment_id, output_path, api),
                )
            )
            or plan
        ),
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.download_attachment_content",
        lambda received_plan, *, api: calls.append(
            ("download_attachment_content", (received_plan, api))
        ),
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.format_attachment_download_result",
        lambda received_plan: (
            calls.append(("format_attachment_download_result", received_plan))
            or "downloaded"
        ),
    )

    result = runner.invoke(
        app,
        ["attachment", "63899", "--output-path", "downloads/"],
    )

    assert result.exit_code == 0
    assert result.stdout == "downloaded\n"
    assert calls == [
        ("validate_attachment_id", "63899"),
        ("get_api", None),
        ("plan_attachment_download", ("63899", "downloads/", api)),
        ("download_attachment_content", (plan, api)),
        ("format_attachment_download_result", plan),
    ]


def test_attachment_command_rejects_empty_ids_before_get_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["attachment", "   "])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == "attachment_id is required and cannot be empty\n"


def test_attachment_command_reports_download_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = object()
    plan = SimpleNamespace(output_file="/tmp/debug.log")

    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.validate_attachment_id",
        lambda attachment_id: None,
    )
    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: api)
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.plan_attachment_download",
        lambda attachment_id, *, output_path, api: plan,
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.download_attachment_content",
        lambda received_plan, *, api: (_ for _ in ()).throw(
            AttachmentDownloadError("download failed")
        ),
    )
    monkeypatch.setattr(
        "jira2ai_core.operations.attachments.format_attachment_download_result",
        lambda received_plan: pytest.fail("format should not be called"),
    )

    result = runner.invoke(app, ["attachment", "63899"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "download failed\n"


def test_create_command_rejects_invalid_fields_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
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
    ("argv", "operation_path", "error", "expected_code"),
    [
        (
            ["read", "PROJ-404"],
            "jira2ai_core.operations.issues.read_issue",
            JiraOperationError("request failed"),
            1,
        ),
        (
            ["projects"],
            "jira2ai_core.operations.projects.list_projects",
            Jira2AIValidationError("bad input"),
            2,
        ),
    ],
)
def test_commands_use_cli_friendly_error_handling(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    operation_path: str,
    error: Exception,
    expected_code: int,
) -> None:
    monkeypatch.setattr("jira2ai_core.client.get_api", lambda: object())

    if operation_path.endswith("read_issue"):
        monkeypatch.setattr(
            operation_path,
            lambda issue_key, *, extra_fields, api: (_ for _ in ()).throw(error),
        )
    else:
        monkeypatch.setattr(
            operation_path,
            lambda query=None, *, api: (_ for _ in ()).throw(error),
        )

    result = runner.invoke(app, argv)

    assert result.exit_code == expected_code
    assert result.stdout == ""
    assert result.stderr == f"{error}\n"


def test_commands_reject_conflicting_output_modes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "jira2ai_core.client.get_api",
        lambda: pytest.fail("get_api should not be called"),
    )

    result = runner.invoke(app, ["read", "PROJ-1", "--json", "--raw"])

    assert result.exit_code == 2
    assert "Use only one of --json or --raw." in result.stderr
