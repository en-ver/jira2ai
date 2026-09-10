from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from mcp.client.stdio import get_default_environment

from . import scenarios
from .conftest import JiraE2EConfig, _private_credentials_file

SYNTHETIC_JIRA_URL = "https://synthetic-jira.invalid"
SYNTHETIC_JIRA_USER = "synthetic-jira-user"
SYNTHETIC_JIRA_TOKEN = "synthetic-jira-token"
SYNTHETIC_CLOUD_SECRET = "synthetic-cloud-secret"
_TESTS_ROOT = Path(__file__).resolve().parents[2]


def _synthetic_config() -> JiraE2EConfig:
    return JiraE2EConfig(
        jira_url=SYNTHETIC_JIRA_URL,
        jira_user=SYNTHETIC_JIRA_USER,
        jira_api_token=SYNTHETIC_JIRA_TOKEN,
        project_key="synthetic-project-control",
        issue_type="synthetic-issue-type-control",
        label="synthetic-label-control",
        issue_key="SYN-1",
        user_query="synthetic-user-query-control",
        worklog_issue_key="SYN-2",
        attachment_id="synthetic-attachment-control",
        allow_write=True,
    )


def test_live_config_repr_omits_credential_values() -> None:
    representation = repr(_synthetic_config())

    for credential in (
        SYNTHETIC_JIRA_URL,
        SYNTHETIC_JIRA_USER,
        SYNTHETIC_JIRA_TOKEN,
    ):
        assert credential not in representation


def test_stdio_credentials_file_is_private_and_excludes_test_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SYNTHETIC_CLOUD_SECRET)
    monkeypatch.setenv("JIRA_E2E_PROJECT_KEY", "parent-project-control")

    with _private_credentials_file(_synthetic_config()) as credentials_file:
        assert credentials_file.is_absolute()
        assert not credentials_file.is_relative_to(_TESTS_ROOT.parent)
        assert json.loads(credentials_file.read_text(encoding="utf-8")) == {
            "url": SYNTHETIC_JIRA_URL,
            "username": SYNTHETIC_JIRA_USER,
            "api_token": SYNTHETIC_JIRA_TOKEN,
        }


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions are required")
def test_stdio_credentials_file_permissions_are_restrictive() -> None:
    with _private_credentials_file(_synthetic_config()) as credentials_file:
        assert stat.S_IMODE(credentials_file.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600


def test_stdio_credentials_file_cleanup_runs_after_success_and_failure() -> None:
    with _private_credentials_file(_synthetic_config()) as credentials_file:
        successful_directory = credentials_file.parent
        assert credentials_file.exists()
    assert not successful_directory.exists()

    with pytest.raises(RuntimeError, match="simulated child startup failure"):
        with _private_credentials_file(_synthetic_config()) as credentials_file:
            failed_directory = credentials_file.parent
            raise RuntimeError("simulated child startup failure")
    assert not failed_directory.exists()


def test_mcp_stdio_environment_excludes_parent_credentials_and_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JIRA_URL", SYNTHETIC_JIRA_URL)
    monkeypatch.setenv("JIRA_USER", SYNTHETIC_JIRA_USER)
    monkeypatch.setenv("JIRA_API_TOKEN", SYNTHETIC_JIRA_TOKEN)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SYNTHETIC_CLOUD_SECRET)
    monkeypatch.setenv("JIRA_E2E_PROJECT_KEY", "parent-project-control")
    monkeypatch.setenv("JIRA_E2E_ALLOW_WRITE", "1")

    child_environment = get_default_environment()

    assert not {
        "JIRA_URL",
        "JIRA_USER",
        "JIRA_API_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "JIRA_E2E_PROJECT_KEY",
        "JIRA_E2E_ALLOW_WRITE",
    }.intersection(child_environment)


def test_stdio_transport_uses_credentials_file_without_parent_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    class RecordedTransport:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SYNTHETIC_CLOUD_SECRET)
    monkeypatch.setenv("JIRA_E2E_PROJECT_KEY", "parent-project-control")
    monkeypatch.setattr(scenarios, "StdioTransport", RecordedTransport)
    credentials_file = tmp_path / "credentials.json"

    scenarios.stdio_transport_mcp(credentials_file=credentials_file, cwd=tmp_path)

    assert captured["args"] == [
        *scenarios.STDIO_ARGS,
        "--credentials-file",
        str(credentials_file.resolve()),
    ]
    assert captured["env"] is None
    assert captured["keep_alive"] is False
    assert captured["cwd"] == str(tmp_path)


def test_uv_project_preserves_caller_cwd_and_selects_local_jira2mcp(
    tmp_path: Path,
) -> None:
    server_cwd = tmp_path / "server-cwd"
    server_cwd.mkdir()
    attachment = server_cwd / "fixture.png"
    attachment.touch()
    assert scenarios.STDIO_ARGS == [
        "--project",
        str(scenarios.REPO_ROOT),
        "run",
        "--package",
        "jira2mcp",
        "jira2mcp",
    ]
    probe = (
        "from pathlib import Path; import json, os, sys, jira2mcp; "
        "print(json.dumps({'cwd': os.getcwd(), "
        "'path': str(Path(sys.argv[1]).resolve()), "
        "'module': str(Path(jira2mcp.__file__).resolve())}))"
    )

    result = subprocess.run(
        [
            scenarios.STDIO_COMMAND,
            "--offline",
            *scenarios.STDIO_ARGS[:-1],
            "python",
            "-c",
            probe,
            attachment.name,
        ],
        capture_output=True,
        check=True,
        cwd=server_cwd,
        text=True,
    )

    assert json.loads(result.stdout) == {
        "cwd": str(server_cwd.resolve()),
        "path": str(attachment.resolve()),
        "module": str(
            scenarios.REPO_ROOT / "packages/jira2mcp/src/jira2mcp/__init__.py"
        ),
    }


def _write_failure_suite(directory: Path) -> None:
    (directory / "conftest.py").write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                f"sys.path.insert(0, {str(_TESTS_ROOT)!r})",
                'pytest_plugins = ("e2e.jira2mcp_e2e.conftest",)',
                "",
                "def pytest_configure(config):",
                '    config.addinivalue_line("markers", "mcp_live: synthetic live test")',
                "    os.environ.update(",
                "        {",
                '            "JIRA_URL": "https://synthetic-jira.invalid",',
                '            "JIRA_USER": "synthetic" + "-jira-user",',
                '            "JIRA_API_TOKEN": "synthetic" + "-jira-token",',
                '            "AWS_SECRET_ACCESS_KEY": "synthetic" + "-cloud-secret",',
                "        }",
                "    )",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (directory / "test_failures.py").write_text(
        """import os

import pytest

pytestmark = pytest.mark.mcp_live


@pytest.fixture
def setup_failure():
    token = os.environ["JIRA_API_TOKEN"]
    cloud_secret = os.environ["AWS_SECRET_ACCESS_KEY"]
    raise RuntimeError("synthetic setup failure")


@pytest.fixture
def teardown_failure():
    token = os.environ["JIRA_API_TOKEN"]
    cloud_secret = os.environ["AWS_SECRET_ACCESS_KEY"]
    yield
    raise RuntimeError("synthetic teardown failure")


def test_setup(setup_failure):
    pass


def test_call():
    token = os.environ["JIRA_API_TOKEN"]
    cloud_secret = os.environ["AWS_SECRET_ACCESS_KEY"]
    raise RuntimeError("synthetic call failure")


def test_teardown(teardown_failure):
    pass
""",
        encoding="utf-8",
    )


def _run_synthetic_live_failures(directory: Path, *, hostile: bool) -> str:
    _write_failure_suite(directory)
    arguments = [sys.executable, "-m", "pytest"]
    if hostile:
        arguments.extend(["--tb=long", "--showlocals", "--full-trace", "-vvv"])

    result = subprocess.run(
        arguments,
        cwd=directory,
        env={
            "HOME": str(directory),
            "PATH": os.environ.get("PATH", ""),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONPATH": str(_TESTS_ROOT),
        },
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == pytest.ExitCode.TESTS_FAILED
    return result.stdout + result.stderr


@pytest.mark.parametrize("hostile", [False, True], ids=["default", "hostile"])
def test_live_failure_reports_hide_synthetic_credentials(
    tmp_path: Path,
    hostile: bool,
) -> None:
    output = _run_synthetic_live_failures(tmp_path, hostile=hostile)

    for marker in (
        "synthetic setup failure",
        "synthetic call failure",
        "synthetic teardown failure",
    ):
        assert marker in output
    for secret in (SYNTHETIC_JIRA_TOKEN, SYNTHETIC_CLOUD_SECRET):
        assert secret not in output
