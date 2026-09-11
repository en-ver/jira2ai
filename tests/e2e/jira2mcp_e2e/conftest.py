from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest

DEFAULT_PROJECT_KEY = "PR"
DEFAULT_ISSUE_TYPE = "Task"
DEFAULT_LABEL = "jira2py-e2e"
LIVE_CREDENTIAL_ENV_VARS = ("JIRA_URL", "JIRA_USER", "JIRA_API_TOKEN")
ALLOW_WRITE_ENV_VAR = "JIRA_E2E_ALLOW_WRITE"
_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class JiraE2EConfig:
    jira_url: str = field(repr=False)
    jira_user: str = field(repr=False)
    jira_api_token: str = field(repr=False)
    project_key: str = DEFAULT_PROJECT_KEY
    issue_type: str = DEFAULT_ISSUE_TYPE
    label: str = DEFAULT_LABEL
    issue_key: str | None = None
    user_query: str | None = None
    worklog_issue_key: str | None = None
    allow_write: bool = False


@contextmanager
def _private_credentials_file(config: JiraE2EConfig) -> Iterator[Path]:
    """Write one stdio server credential file outside the checkout."""
    with tempfile.TemporaryDirectory(prefix="jira2mcp-e2e-") as directory:
        credentials_directory = Path(directory).resolve()
        try:
            credentials_directory.relative_to(_REPO_ROOT)
        except ValueError:
            pass
        else:
            raise RuntimeError(
                "Refusing to create live credentials inside the checkout"
            )

        if os.name == "posix":
            credentials_directory.chmod(0o700)

        credentials_file = credentials_directory / "credentials.json"
        descriptor = os.open(
            credentials_file,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            stream = os.fdopen(descriptor, "w", encoding="utf-8")
        except BaseException:
            os.close(descriptor)
            raise

        with stream:
            json.dump(
                {
                    "url": config.jira_url,
                    "username": config.jira_user,
                    "api_token": config.jira_api_token,
                },
                stream,
            )
            stream.write("\n")

        if os.name == "posix":
            credentials_file.chmod(0o600)

        yield credentials_file


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[None],
) -> Generator[None]:
    """Keep live-test tracebacks from rendering fixture arguments or locals."""
    if item.get_closest_marker("mcp_live") is None:
        yield
        return

    options = item.config.option
    original_options = {
        "fulltrace": options.fulltrace,
        "showlocals": options.showlocals,
        "tbstyle": options.tbstyle,
    }
    options.fulltrace = False
    options.showlocals = False
    options.tbstyle = "short"
    try:
        yield
    finally:
        for name, value in original_options.items():
            setattr(options, name, value)


def _env(name: str, *, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _missing_live_credentials() -> list[str]:
    return [name for name in LIVE_CREDENTIAL_ENV_VARS if not _env(name)]


def _skip_for_missing_optional(name: str) -> None:
    pytest.skip(f"Set {name} to run this live MCP test.")


@pytest.fixture(autouse=True)
def _skip_live_tests_without_credentials(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("mcp_live") is None:
        return

    missing = _missing_live_credentials()
    if missing:
        pytest.skip("Missing Jira live test credentials: " + ", ".join(missing))


@pytest.fixture(autouse=True)
def _skip_write_tests_without_opt_in(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("mcp_write") is None:
        return

    if _env(ALLOW_WRITE_ENV_VAR) != "1":
        pytest.skip(f"Set {ALLOW_WRITE_ENV_VAR}=1 to run mcp_write tests.")


@pytest.fixture
def jira_e2e_config() -> JiraE2EConfig:
    missing = _missing_live_credentials()
    if missing:
        pytest.skip("Missing Jira live test credentials: " + ", ".join(missing))

    jira_url = _env("JIRA_URL")
    jira_user = _env("JIRA_USER")
    jira_api_token = _env("JIRA_API_TOKEN")
    if jira_url is None or jira_user is None or jira_api_token is None:
        raise AssertionError("missing live Jira credentials should have skipped")

    return JiraE2EConfig(
        jira_url=jira_url,
        jira_user=jira_user,
        jira_api_token=jira_api_token,
        project_key=_env("JIRA_E2E_PROJECT_KEY", default=DEFAULT_PROJECT_KEY)
        or DEFAULT_PROJECT_KEY,
        issue_type=_env("JIRA_E2E_ISSUE_TYPE", default=DEFAULT_ISSUE_TYPE)
        or DEFAULT_ISSUE_TYPE,
        label=_env("JIRA_E2E_LABEL", default=DEFAULT_LABEL) or DEFAULT_LABEL,
        issue_key=_env("JIRA_E2E_ISSUE_KEY"),
        user_query=_env("JIRA_E2E_USER_QUERY"),
        worklog_issue_key=_env("JIRA_E2E_WORKLOG_ISSUE_KEY"),
        allow_write=_env(ALLOW_WRITE_ENV_VAR) == "1",
    )


@pytest.fixture
def jira_e2e_credentials_file(
    jira_e2e_config: JiraE2EConfig,
) -> Generator[Path]:
    with _private_credentials_file(jira_e2e_config) as credentials_file:
        yield credentials_file


@pytest.fixture
def jira_e2e_project_key(jira_e2e_config: JiraE2EConfig) -> str:
    return jira_e2e_config.project_key


@pytest.fixture
def jira_e2e_issue_type(jira_e2e_config: JiraE2EConfig) -> str:
    return jira_e2e_config.issue_type


@pytest.fixture
def jira_e2e_label(jira_e2e_config: JiraE2EConfig) -> str:
    return jira_e2e_config.label


@pytest.fixture
def jira_e2e_issue_key(jira_e2e_config: JiraE2EConfig) -> str | None:
    return jira_e2e_config.issue_key


@pytest.fixture
def jira_e2e_required_issue_key(jira_e2e_issue_key: str | None) -> str:
    if jira_e2e_issue_key is None:
        _skip_for_missing_optional("JIRA_E2E_ISSUE_KEY")
    return jira_e2e_issue_key


@pytest.fixture
def jira_e2e_user_query(jira_e2e_config: JiraE2EConfig) -> str | None:
    return jira_e2e_config.user_query


@pytest.fixture
def jira_e2e_required_user_query(jira_e2e_user_query: str | None) -> str:
    if jira_e2e_user_query is None:
        _skip_for_missing_optional("JIRA_E2E_USER_QUERY")
    return jira_e2e_user_query


@pytest.fixture
def jira_e2e_worklog_issue_key(jira_e2e_config: JiraE2EConfig) -> str | None:
    return jira_e2e_config.worklog_issue_key


@pytest.fixture
def jira_e2e_required_worklog_issue_key(
    jira_e2e_worklog_issue_key: str | None,
) -> str:
    if jira_e2e_worklog_issue_key is None:
        _skip_for_missing_optional("JIRA_E2E_WORKLOG_ISSUE_KEY")
    return jira_e2e_worklog_issue_key
