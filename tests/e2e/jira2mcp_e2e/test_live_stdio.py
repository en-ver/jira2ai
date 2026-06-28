from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest

from .scenarios import (
    REPO_ROOT,
    assert_contains_names,
    assert_non_error_result,
    assert_structured_content,
    call_tool_mcp,
    list_tools_mcp,
    stdio_client_mcp,
    tool_names,
)

pytestmark = [pytest.mark.mcp_live, pytest.mark.mcp_stdio]

EXPECTED_JIRA_TOOLS = [
    "jira_add_link",
    "jira_add_worklog",
    "jira_attachment",
    "jira_attachment_metadata",
    "jira_attachments",
    "jira_auth_status",
    "jira_comment",
    "jira_comments",
    "jira_create",
    "jira_delete_attachment",
    "jira_delete_comment",
    "jira_delete_link",
    "jira_delete_worklog",
    "jira_download_attachment",
    "jira_edit",
    "jira_fields",
    "jira_filters",
    "jira_issue_links",
    "jira_me",
    "jira_priorities",
    "jira_project",
    "jira_projects",
    "jira_read",
    "jira_run_filter",
    "jira_search",
    "jira_statuses",
    "jira_transition",
    "jira_transitions",
    "jira_update_comment",
    "jira_update_worklog",
    "jira_upload_attachment",
    "jira_users",
    "jira_worklog_report",
    "jira_worklogs",
]


def _run(awaitable):
    return asyncio.run(awaitable)


def test_stdio_smoke_lists_expected_tools(jira_e2e_stdio_env: dict[str, str]) -> None:
    async def scenario() -> None:
        async with stdio_client_mcp(
            env=jira_e2e_stdio_env,
            cwd=REPO_ROOT,
            timeout=30,
        ) as client:
            tools = await list_tools_mcp(client)
            assert_contains_names(tool_names(tools), EXPECTED_JIRA_TOOLS)

    _run(scenario())


def test_stdio_smoke_calls_safe_read_only_tool(
    jira_e2e_stdio_env: dict[str, str],
    jira_e2e_project_key: str,
) -> None:
    async def scenario() -> None:
        async with stdio_client_mcp(
            env=jira_e2e_stdio_env,
            cwd=REPO_ROOT,
            timeout=30,
        ) as client:
            result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_projects",
                    {"query": jira_e2e_project_key, "raw": True},
                )
            )
            payload = assert_structured_content(result)
            values = payload.get("values")
            if not isinstance(values, list):
                raise AssertionError(
                    "Expected jira_projects raw payload to include values"
                )
            assert any(
                isinstance(project, Mapping)
                and project.get("key") == jira_e2e_project_key
                for project in values
            )

    _run(scenario())
