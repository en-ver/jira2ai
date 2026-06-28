from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import date

import pytest

from .conftest import JiraE2EConfig
from .scenarios import (
    assert_contains_names,
    assert_non_error_result,
    assert_result_data,
    assert_structured_content,
    call_tool_mcp,
    get_prompt_mcp,
    inmemory_client_mcp,
    list_prompts_mcp,
    list_resources_mcp,
    list_tools_mcp,
    parse_result_json,
    prompt_names,
    read_resource_mcp,
    require_prompt_text,
    require_resource_text,
    require_text_content,
    resource_uris,
    structured_content,
    tool_names,
)

pytestmark = pytest.mark.mcp_live

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


def _label_search_jql(config: JiraE2EConfig) -> str:
    return (
        f'project = {config.project_key} AND labels = "{config.label}" '
        "ORDER BY created DESC"
    )


def _issues_from_search_payload(
    payload: Mapping[str, object],
) -> list[Mapping[str, object]]:
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise AssertionError(
            "Expected jira_search raw payload to include an issues list"
        )

    normalized: list[Mapping[str, object]] = []
    for issue in issues:
        if not isinstance(issue, Mapping):
            raise AssertionError("Expected each search issue to be a mapping")
        normalized.append(issue)
    return normalized


async def _search_labeled_issues(
    client, config: JiraE2EConfig
) -> list[Mapping[str, object]]:
    result = assert_non_error_result(
        await call_tool_mcp(
            client,
            "jira_search",
            {
                "jql": _label_search_jql(config),
                "max_results": 10,
                "raw": True,
            },
        )
    )
    payload = assert_structured_content(result)
    return _issues_from_search_payload(payload)


async def _resolve_issue_key(client, config: JiraE2EConfig) -> str | None:
    if config.issue_key:
        return config.issue_key

    issues = await _search_labeled_issues(client, config)
    if not issues:
        return None

    issue_key = issues[0].get("key")
    if not isinstance(issue_key, str) or not issue_key:
        raise AssertionError(
            "Expected discovered Jira issue to include a non-empty key"
        )
    return issue_key


def test_inmemory_registry_prompt_and_resource_surfaces() -> None:
    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=20) as client:
            tools = await list_tools_mcp(client)
            assert_contains_names(tool_names(tools), EXPECTED_JIRA_TOOLS)

            prompts = await list_prompts_mcp(client)
            assert_contains_names(prompt_names(prompts), ["jira_jql_syntax"])

            prompt = await get_prompt_mcp(client, "jira_jql_syntax")
            prompt_text = require_prompt_text(prompt)
            assert "JQL" in prompt_text
            assert "ORDER BY" in prompt_text

            resources = await list_resources_mcp(client)
            assert_contains_names(resource_uris(resources), ["data://jira/link-types"])

            resource = await read_resource_mcp(client, "data://jira/link-types")
            resource_text = require_resource_text(resource)
            assert "outward=" in resource_text
            assert "inward=" in resource_text

    _run(scenario())


def test_inmemory_read_only_metadata_tools(jira_e2e_config: JiraE2EConfig) -> None:
    async def scenario() -> None:
        user_query = jira_e2e_config.user_query or jira_e2e_config.jira_user

        async with inmemory_client_mcp(timeout=20) as client:
            projects_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_projects",
                    {"query": jira_e2e_config.project_key, "raw": True},
                )
            )
            projects_payload = assert_structured_content(projects_result)
            project_values = projects_payload.get("values")
            if not isinstance(project_values, list):
                raise AssertionError(
                    "Expected jira_projects raw payload to include values"
                )
            assert any(
                isinstance(project, Mapping)
                and project.get("key") == jira_e2e_config.project_key
                for project in project_values
            )

            issue_types_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_fields",
                    {"project_key": jira_e2e_config.project_key},
                )
            )
            issue_types_text = require_text_content(issue_types_result)
            assert jira_e2e_config.project_key in issue_types_text
            assert "Issue types" in issue_types_text

            create_fields_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_fields",
                    {
                        "project_key": jira_e2e_config.project_key,
                        "issue_type": jira_e2e_config.issue_type,
                    },
                )
            )
            create_fields_text = require_text_content(create_fields_result)
            assert jira_e2e_config.project_key in create_fields_text
            assert jira_e2e_config.issue_type in create_fields_text

            users_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_users",
                    {"query": user_query},
                )
            )
            users_text = require_text_content(users_result)
            assert users_text.startswith("Found ")
            if "0 user(s)" not in users_text:
                assert "accountId:" in users_text

    _run(scenario())


def test_inmemory_search_supports_labeled_issue_queries(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=20) as client:
            issues = await _search_labeled_issues(client, jira_e2e_config)
            assert len(issues) <= 10

    _run(scenario())


def test_inmemory_read_and_comments_use_fixture_or_discovered_issue(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=20) as client:
            issue_key = await _resolve_issue_key(client, jira_e2e_config)
            if issue_key is None:
                pytest.skip(
                    "Set JIRA_E2E_ISSUE_KEY or seed a labeled jira2py-e2e issue "
                    "to exercise jira_read and jira_comments."
                )

            read_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_read",
                    {"issue_key": issue_key, "raw": True},
                )
            )
            read_payload = assert_structured_content(read_result)
            assert read_payload.get("key") == issue_key

            comments_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_comments",
                    {"issue_key": issue_key, "raw": True},
                )
            )
            comments_payload = assert_structured_content(comments_result)
            comments = comments_payload.get("comments")
            if not isinstance(comments, list):
                raise AssertionError(
                    "Expected jira_comments raw payload to include comments"
                )
            total = comments_payload.get("total")
            assert total is None or isinstance(total, int)

    _run(scenario())


def test_inmemory_worklog_report_uses_fixture_or_discovered_issue(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=20) as client:
            issue_key = jira_e2e_config.worklog_issue_key or jira_e2e_config.issue_key
            if issue_key is None:
                issue_key = await _resolve_issue_key(client, jira_e2e_config)
            if issue_key is None:
                pytest.skip(
                    "Set JIRA_E2E_WORKLOG_ISSUE_KEY, JIRA_E2E_ISSUE_KEY, or seed a "
                    "labeled jira2py-e2e issue to exercise jira_worklog_report."
                )

            worklog_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_worklog_report",
                    {
                        "start_date": "2020-01-01",
                        "end_date": date.today().isoformat(),
                        "jql": f"issue = {issue_key}",
                        "raw": True,
                    },
                )
            )
            worklog_payload = assert_structured_content(worklog_result)
            if "rowCount" in worklog_payload:
                assert isinstance(worklog_payload["rowCount"], int)
            if "rows" in worklog_payload:
                assert isinstance(worklog_payload["rows"], list)

    _run(scenario())


def test_inmemory_fields_raw_list_output_round_trips_via_structured_content(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=20) as client:
            result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_fields",
                    {
                        "project_key": jira_e2e_config.project_key,
                        "issue_type": jira_e2e_config.issue_type,
                        "raw": True,
                    },
                )
            )
            wrapped_payload = assert_structured_content(result)
            payload = assert_result_data(result, list)
            assert wrapped_payload.get("data") == payload
            assert parse_result_json(result) == payload
            assert payload
            assert all(isinstance(field, Mapping) for field in payload)

    _run(scenario())


def test_inmemory_users_raw_list_output_round_trips_via_structured_content(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    async def scenario() -> None:
        user_query = jira_e2e_config.user_query or jira_e2e_config.jira_user

        async with inmemory_client_mcp(timeout=20) as client:
            result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_users",
                    {"query": user_query, "raw": True},
                )
            )
            wrapped_payload = structured_content(result)
            if not isinstance(wrapped_payload, Mapping):
                raise AssertionError(
                    "Expected jira_users raw structuredContent to be a dict wrapper"
                )
            payload = assert_result_data(result, list)
            assert wrapped_payload.get("data") == payload
            assert parse_result_json(result) == payload
            assert all(isinstance(user, Mapping) for user in payload)
            if payload:
                assert isinstance(payload[0].get("accountId"), str)

    _run(scenario())
