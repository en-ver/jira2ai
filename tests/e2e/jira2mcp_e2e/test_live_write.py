from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from time import monotonic
from uuid import uuid4

import pytest

from .conftest import JiraE2EConfig
from .scenarios import (
    assert_non_error_result,
    assert_structured_content,
    build_create_fields_from_metadata_mcp,
    call_tool_mcp,
    inmemory_client_mcp,
    read_resource_mcp,
    require_resource_text,
    require_text_content,
)

pytestmark = [pytest.mark.mcp_live, pytest.mark.mcp_write]

_SEARCH_INDEX_TIMEOUT_SECONDS = 20.0
_SEARCH_INDEX_POLL_SECONDS = 2.0


def _run(awaitable):
    return asyncio.run(awaitable)


def _search_jql(config: JiraE2EConfig, expected_keys: set[str]) -> str:
    ordered_keys = '", "'.join(sorted(expected_keys))
    return (
        f"project = {config.project_key} "
        f'AND labels = "{config.label}" '
        f'AND key in ("{ordered_keys}") '
        "ORDER BY created DESC"
    )


async def _search_for_expected_issue_keys(
    client,
    jira_e2e_config: JiraE2EConfig,
    expected_keys: set[str],
    *,
    timeout_seconds: float = _SEARCH_INDEX_TIMEOUT_SECONDS,
    poll_seconds: float = _SEARCH_INDEX_POLL_SECONDS,
) -> set[str]:
    deadline = monotonic() + timeout_seconds
    last_payload: Mapping[str, object] | None = None
    last_found_keys: set[str] = set()
    jql = _search_jql(jira_e2e_config, expected_keys)

    while True:
        search_result = assert_non_error_result(
            await call_tool_mcp(
                client,
                "jira_search",
                {
                    "jql": jql,
                    "max_results": 10,
                    "raw": True,
                },
            )
        )
        payload = assert_structured_content(search_result)
        last_payload = payload
        last_found_keys = _issue_keys_from_search_payload(payload)
        missing_keys = expected_keys - last_found_keys
        if not missing_keys:
            return last_found_keys

        remaining = deadline - monotonic()
        if remaining <= 0:
            raise AssertionError(
                "jira_search did not return expected created issues within "
                f"{timeout_seconds:.0f}s. Expected keys: {sorted(expected_keys)}. "
                f"Missing keys: {sorted(missing_keys)}. "
                f"Last observed keys: {sorted(last_found_keys)}. "
                f"Last observed payload: {last_payload!r}"
            )

        await asyncio.sleep(min(poll_seconds, remaining))


def _issue_key_from_payload(payload: Mapping[str, object]) -> str:
    issue_key = payload.get("key")
    if not isinstance(issue_key, str) or not issue_key:
        raise AssertionError(
            "Expected Jira tool payload to include a non-empty issue key"
        )
    return issue_key


def _issue_keys_from_search_payload(payload: Mapping[str, object]) -> set[str]:
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise AssertionError(
            "Expected jira_search raw payload to include an issues list"
        )

    issue_keys: set[str] = set()
    for issue in issues:
        if not isinstance(issue, Mapping):
            raise AssertionError("Expected each search issue to be a mapping")
        issue_key = issue.get("key")
        if isinstance(issue_key, str) and issue_key:
            issue_keys.add(issue_key)
    return issue_keys


def _labels_from_issue_payload(payload: Mapping[str, object]) -> list[str]:
    fields = payload.get("fields")
    if not isinstance(fields, Mapping):
        raise AssertionError("Expected jira_read payload to include fields")

    labels = fields.get("labels")
    if not isinstance(labels, list):
        raise AssertionError("Expected jira_read payload to include labels")
    if not all(isinstance(label, str) for label in labels):
        raise AssertionError("Expected every Jira label to be a string")
    return list(labels)


def _json_contains_text(value: object, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, Mapping):
        return any(_json_contains_text(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(_json_contains_text(item, needle) for item in value)
    return False


def _first_link_type(resource_text: str) -> str:
    match = re.search(r"\*\*(.+?)\*\*", resource_text)
    if match is None:
        raise AssertionError(
            "Expected link-types resource text to include a markdown link name"
        )
    return match.group(1)


def _with_test_label(fields: dict[str, object], label: str) -> dict[str, object]:
    updated = dict(fields)
    existing = updated.get("labels")
    if existing is None:
        updated["labels"] = [label]
        return updated
    if not isinstance(existing, list) or not all(
        isinstance(item, str) for item in existing
    ):
        raise AssertionError(
            "Expected jira_create labels field to be a list of strings"
        )
    if label not in existing:
        updated["labels"] = [*existing, label]
    return updated


def _link_id_for_issue(payload: Mapping[str, object], other_issue_key: str) -> str:
    fields = payload.get("fields")
    if not isinstance(fields, Mapping):
        raise AssertionError("Expected jira_read payload to include fields")

    issue_links = fields.get("issuelinks")
    if not isinstance(issue_links, list):
        raise AssertionError("Expected jira_read payload to include issuelinks")

    for issue_link in issue_links:
        if not isinstance(issue_link, Mapping):
            continue
        for side in ("outwardIssue", "inwardIssue"):
            linked_issue = issue_link.get(side)
            if not isinstance(linked_issue, Mapping):
                continue
            if linked_issue.get("key") != other_issue_key:
                continue
            link_id = issue_link.get("id")
            if isinstance(link_id, str) and link_id:
                return link_id
            if isinstance(link_id, int):
                return str(link_id)

    raise AssertionError(
        f"Could not find an issue link from the raw payload to {other_issue_key}"
    )


def test_write_issue_lifecycle_creates_two_tasks_and_leaves_them_in_jira(
    jira_e2e_config: JiraE2EConfig,
) -> None:
    token = uuid4().hex[:8]
    primary_summary = f"jira2mcp e2e primary {token}"
    secondary_summary = f"jira2mcp e2e secondary {token}"
    edited_summary = f"{primary_summary} [edited]"
    comment_text = f"jira2mcp mcp_write comment {token}"

    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=30) as client:
            create_fields = _with_test_label(
                await build_create_fields_from_metadata_mcp(client, jira_e2e_config),
                jira_e2e_config.label,
            )

            first_create = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_create",
                    {
                        "project_key": jira_e2e_config.project_key,
                        "issue_type": jira_e2e_config.issue_type,
                        "summary": primary_summary,
                        "description": f"Created by jira2mcp mcp_write {token}",
                        "fields": create_fields,
                        "raw": True,
                    },
                )
            )
            first_key = _issue_key_from_payload(assert_structured_content(first_create))

            second_create = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_create",
                    {
                        "project_key": jira_e2e_config.project_key,
                        "issue_type": jira_e2e_config.issue_type,
                        "summary": secondary_summary,
                        "description": f"Created by jira2mcp mcp_write {token}",
                        "fields": create_fields,
                        "raw": True,
                    },
                )
            )
            second_key = _issue_key_from_payload(
                assert_structured_content(second_create)
            )
            assert first_key != second_key

            first_read = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_read",
                    {"issue_key": first_key, "fields": ["labels"]},
                )
            )
            first_read_payload = assert_structured_content(first_read)
            assert first_read_payload.get("key") == first_key
            assert jira_e2e_config.label in _labels_from_issue_payload(
                first_read_payload
            )

            second_read = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_read",
                    {"issue_key": second_key, "fields": ["labels"]},
                )
            )
            second_read_payload = assert_structured_content(second_read)
            assert second_read_payload.get("key") == second_key
            assert jira_e2e_config.label in _labels_from_issue_payload(
                second_read_payload
            )

            found_keys = await _search_for_expected_issue_keys(
                client,
                jira_e2e_config,
                {first_key, second_key},
            )
            assert {first_key, second_key}.issubset(found_keys)

            edit_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_edit",
                    {
                        "issue_key": first_key,
                        "summary": edited_summary,
                        "description": f"Updated by jira2mcp mcp_write {token}",
                        "raw": True,
                    },
                )
            )
            edit_payload = assert_structured_content(edit_result)
            assert edit_payload.get("key") == first_key or edit_payload.get("id")

            updated_read = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_read",
                    {"issue_key": first_key, "fields": ["summary"]},
                )
            )
            updated_payload = assert_structured_content(updated_read)
            updated_fields = updated_payload.get("fields")
            if not isinstance(updated_fields, Mapping):
                raise AssertionError("Expected jira_read payload to include fields")
            assert updated_fields.get("summary") == edited_summary

            comment_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_comment",
                    {
                        "issue_key": first_key,
                        "body": comment_text,
                        "raw": True,
                    },
                )
            )
            comment_payload = assert_structured_content(comment_result)
            assert comment_payload.get("id")

            comments_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_comments",
                    {
                        "issue_key": first_key,
                        "order_by": "-created",
                        "max_results": 10,
                        "raw": True,
                    },
                )
            )
            comments_payload = assert_structured_content(comments_result)
            assert _json_contains_text(comments_payload, comment_text)

            link_types_resource = await read_resource_mcp(
                client, "data://jira/link-types"
            )
            link_type = _first_link_type(require_resource_text(link_types_resource))

            add_link_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_add_link",
                    {
                        "link_type": link_type,
                        "outward_issue_key": first_key,
                        "inward_issue_key": second_key,
                        "raw": True,
                    },
                )
            )
            add_link_payload = assert_structured_content(add_link_result)
            assert add_link_payload.get("link_type") == link_type

            linked_read = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_read",
                    {"issue_key": first_key, "fields": ["issuelinks"]},
                )
            )
            link_id = _link_id_for_issue(
                assert_structured_content(linked_read), second_key
            )

            delete_link_result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_delete_link",
                    {"link_id": link_id, "raw": True},
                )
            )
            delete_link_payload = assert_structured_content(delete_link_result)
            assert str(delete_link_payload.get("link_id")) == link_id

    _run(scenario())


def test_write_module_can_download_fixture_attachment_when_configured(
    jira_e2e_required_attachment_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    download_dir = tmp_path / "downloads"
    monkeypatch.chdir(tmp_path)

    async def scenario() -> None:
        async with inmemory_client_mcp(timeout=30) as client:
            result = assert_non_error_result(
                await call_tool_mcp(
                    client,
                    "jira_attachment",
                    {
                        "attachment_id": jira_e2e_required_attachment_id,
                        "output_path": "downloads",
                    },
                )
            )
            text = require_text_content(result)
            assert "Downloaded:" in text
            assert "Saved to:" in text

    _run(scenario())

    assert download_dir.exists()
    assert any(download_dir.iterdir())
