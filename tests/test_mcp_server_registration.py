from __future__ import annotations

import asyncio
from typing import Any, cast

from jira2mcp import mcp

EXPECTED_JIRA_TOOLS = {
    "jira_add_link",
    "jira_add_worklog",
    "jira_attachment",
    "jira_attachment_metadata",
    "jira_attachments",
    "jira_auth_status",
    "jira_changelogs",
    "jira_changelogs_by_ids",
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
}


def test_mcp_registers_existing_and_new_jira_tools() -> None:
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}

    assert EXPECTED_JIRA_TOOLS <= names


def test_read_tool_requires_nonempty_field_selectors() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    tool = next(tool for tool in tools if tool.name == "jira_read")
    parameters = cast(dict[str, Any], tool.parameters)
    properties = cast(dict[str, dict[str, Any]], parameters["properties"])

    assert set(parameters["required"]) == {"issue_key", "fields"}
    assert set(properties) == {"issue_key", "fields"}
    assert parameters["additionalProperties"] is False

    issue_key = properties["issue_key"]
    assert issue_key["type"] == "string"
    assert issue_key["minLength"] == 1

    fields = properties["fields"]
    assert fields["type"] == "array"
    assert fields["minItems"] == 1
    assert "default" not in fields

    item = fields["items"]
    assert item["type"] == "string"
    assert item["minLength"] == 1
    assert "pattern" in item
    assert "comma" in item["description"].lower()


def test_changelog_tools_expose_complete_history_and_known_id_schemas() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    expected = {
        "jira_changelogs": (
            {"issue_key"},
            {"issue_key", "created_at_or_after", "created_before", "raw"},
        ),
        "jira_changelogs_by_ids": (
            {"issue_key", "changelog_ids"},
            {"issue_key", "changelog_ids", "raw"},
        ),
    }

    for name, (required, property_names) in expected.items():
        tool = next(tool for tool in tools if tool.name == name)
        parameters = cast(dict[str, Any], tool.parameters)
        properties = cast(dict[str, dict[str, Any]], parameters["properties"])

        assert set(parameters["required"]) == required
        assert set(properties) == property_names
        assert parameters["additionalProperties"] is False
        assert properties["issue_key"]["type"] == "string"
        assert properties["raw"] == {
            "default": False,
            "description": properties["raw"]["description"],
            "type": "boolean",
        }

    complete_history = next(tool for tool in tools if tool.name == "jira_changelogs")
    complete_properties = cast(
        dict[str, dict[str, Any]], complete_history.parameters["properties"]
    )
    for name in ("created_at_or_after", "created_before"):
        assert {entry["type"] for entry in complete_properties[name]["anyOf"]} == {
            "string",
            "null",
        }
        assert complete_properties[name]["default"] is None
        assert "complete history" in complete_properties[name]["description"].lower()

    by_ids = next(tool for tool in tools if tool.name == "jira_changelogs_by_ids")
    by_ids_properties = cast(dict[str, dict[str, Any]], by_ids.parameters["properties"])
    changelog_ids = by_ids_properties["changelog_ids"]
    assert changelog_ids["type"] == "array"
    assert changelog_ids["minItems"] == 1
    assert changelog_ids["items"] == {"type": "integer"}


def test_search_tools_expose_manual_cursor_paging_schema() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    expected = {
        "jira_search": (
            {"jql"},
            {"jql", "max_results", "fields", "next_page_token", "raw"},
        ),
        "jira_run_filter": (
            {"filter_id"},
            {"filter_id", "max_results", "fields", "next_page_token", "raw"},
        ),
    }

    for name, (required, property_names) in expected.items():
        tool = next(tool for tool in tools if tool.name == name)
        parameters = cast(dict[str, Any], tool.parameters)
        properties = cast(dict[str, dict[str, Any]], parameters["properties"])

        assert "exactly one page" in tool.description.lower()
        assert set(parameters["required"]) == required
        assert set(properties) == property_names
        assert parameters["additionalProperties"] is False

        token = properties["next_page_token"]
        assert {entry["type"] for entry in token["anyOf"]} == {"string", "null"}
        assert token["default"] is None
        token_description = token["description"].lower()
        assert "opaque" in token_description
        assert "nextpagetoken" in token_description
        assert "forwarded unchanged" in token_description
        assert "stable" in token_description

        max_results = properties["max_results"]
        assert max_results["type"] == "integer"
        assert max_results["default"] == 20
        assert max_results["minimum"] == 1
        assert max_results["maximum"] == 50
        assert "per page" in max_results["description"].lower()

        fields = properties["fields"]
        array_schema = next(
            entry for entry in fields["anyOf"] if entry["type"] == "array"
        )
        assert array_schema["items"]["type"] == "string"
        assert fields["default"] is None
        fields_description = fields["description"].lower()
        for field in (
            "summary",
            "status",
            "assignee",
            "priority",
            "issuetype",
            "created",
            "updated",
        ):
            assert field in fields_description
        assert "whole-field" in fields_description
        assert "identity" in fields_description
        assert "email" in fields_description
        assert "avatar" in fields_description

        raw = properties["raw"]
        assert raw["type"] == "boolean"
        assert raw["default"] is False
        raw_description = raw["description"].lower()
        assert "api-shaped" in raw_description
        assert "structured content" in raw_description
        assert "json text fallback" in raw_description
        assert "nextpagetoken" in raw_description
        assert "30,000" in raw_description
        assert "client" in raw_description
