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
    "jira_list_fields",
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
    assert "[~accountId:<id>]" in mcp.instructions
    assert (
        "escaped, malformed, code, link, and image forms stay text" in mcp.instructions
    )
    assert "presentation-only" in mcp.instructions
    assert "jira_read structured data" in mcp.instructions
    assert (
        "jira_transition.update comment bodies must already be ADF" in mcp.instructions
    )


def test_mcp_high_level_write_tools_describe_canonical_mentions() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    descriptions = {tool.name: tool.description for tool in tools}

    for name in {
        "jira_create",
        "jira_edit",
        "jira_comment",
        "jira_update_comment",
        "jira_add_worklog",
        "jira_update_worklog",
    }:
        assert "[~accountId:<id>]" in descriptions[name]


def test_transition_tools_expose_native_workflow_schemas_and_annotations() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    discovery = next(tool for tool in tools if tool.name == "jira_transitions")
    mutation = next(tool for tool in tools if tool.name == "jira_transition")

    discovery_parameters = cast(dict[str, Any], discovery.parameters)
    discovery_properties = cast(
        dict[str, dict[str, Any]], discovery_parameters["properties"]
    )
    assert set(discovery_parameters["required"]) == {"issue_key"}
    assert set(discovery_properties) == {
        "issue_key",
        "transition_id",
        "include_unavailable_transitions",
        "raw",
    }
    assert discovery_parameters["additionalProperties"] is False
    assert discovery_properties["transition_id"]["default"] is None
    assert {
        entry["type"] for entry in discovery_properties["transition_id"]["anyOf"]
    } == {
        "string",
        "null",
    }
    assert discovery_properties["include_unavailable_transitions"] == {
        "default": False,
        "description": discovery_properties["include_unavailable_transitions"][
            "description"
        ],
        "type": "boolean",
    }
    assert (
        "diagnostic"
        in discovery_properties["include_unavailable_transitions"][
            "description"
        ].lower()
    )
    assert discovery.annotations.readOnlyHint is True
    assert discovery.annotations.idempotentHint is True

    mutation_parameters = cast(dict[str, Any], mutation.parameters)
    mutation_properties = cast(
        dict[str, dict[str, Any]], mutation_parameters["properties"]
    )
    assert set(mutation_parameters["required"]) == {"issue_key", "transition"}
    assert set(mutation_properties) == {
        "issue_key",
        "transition",
        "fields",
        "update",
        "raw",
    }
    assert mutation_parameters["additionalProperties"] is False
    for field_name in ("fields", "update"):
        schema = mutation_properties[field_name]
        assert schema["default"] is None
        assert {entry["type"] for entry in schema["anyOf"]} == {"object", "null"}
        assert "native jira" in schema["description"].lower()
        assert "history" not in schema["description"].lower()
        assert "entity" not in schema["description"].lower()
    assert mutation.annotations.readOnlyHint is False
    assert mutation.annotations.destructiveHint is True
    assert mutation.annotations.idempotentHint is False
    assert "status id" in discovery.description.lower()
    assert "204" in mutation.description
    assert "blindly retry" in mutation.description.lower()


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
            {
                "issue_key",
                "created_at_or_after",
                "created_before",
                "field_ids",
                "result_start_at",
                "result_max_results",
                "raw",
            },
        ),
        "jira_changelogs_by_ids": (
            {"issue_key", "changelog_ids"},
            {"issue_key", "changelog_ids", "field_ids", "raw"},
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

    field_ids = complete_properties["field_ids"]
    field_ids_array = next(
        entry for entry in field_ids["anyOf"] if entry["type"] == "array"
    )
    assert field_ids["default"] is None
    assert field_ids_array["minItems"] == 1
    assert field_ids_array["items"]["type"] == "string"
    assert field_ids_array["items"]["minLength"] == 1
    assert "fieldid" in field_ids["description"].lower()

    result_start_at = complete_properties["result_start_at"]
    assert result_start_at["default"] == 0
    assert result_start_at["minimum"] == 0
    assert "complete history" in result_start_at["description"].lower()

    result_max_results = complete_properties["result_max_results"]
    assert result_max_results["default"] is None
    assert {entry["type"] for entry in result_max_results["anyOf"]} == {
        "integer",
        "null",
    }
    assert (
        next(
            entry for entry in result_max_results["anyOf"] if entry["type"] == "integer"
        )["minimum"]
        == 1
    )

    by_ids = next(tool for tool in tools if tool.name == "jira_changelogs_by_ids")
    by_ids_properties = cast(dict[str, dict[str, Any]], by_ids.parameters["properties"])
    changelog_ids = by_ids_properties["changelog_ids"]
    assert changelog_ids["type"] == "array"
    assert changelog_ids["minItems"] == 1
    assert changelog_ids["items"] == {"type": "integer"}
    by_ids_field_ids = by_ids_properties["field_ids"]
    assert by_ids_field_ids["default"] is None
    assert "result_start_at" not in by_ids_properties
    assert "result_max_results" not in by_ids_properties


def test_list_fields_tool_exposes_one_server_page_schema() -> None:
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    tool = next(tool for tool in tools if tool.name == "jira_list_fields")
    parameters = cast(dict[str, Any], tool.parameters)
    properties = cast(dict[str, dict[str, Any]], parameters["properties"])

    assert set(parameters.get("required", [])) == set()
    assert set(properties) == {
        "project_key",
        "query",
        "field_ids",
        "field_types",
        "start_at",
        "max_results",
        "raw",
    }
    assert parameters["additionalProperties"] is False
    assert "one searchable jira field catalog page" in tool.description.lower()
    assert "screen applicability" in tool.description.lower()

    for name in ("project_key", "query"):
        assert {entry["type"] for entry in properties[name]["anyOf"]} == {
            "string",
            "null",
        }
        assert properties[name]["default"] is None

    field_ids = properties["field_ids"]
    field_ids_array = next(
        entry for entry in field_ids["anyOf"] if entry["type"] == "array"
    )
    assert field_ids["default"] is None
    assert field_ids_array["minItems"] == 1
    assert field_ids_array["items"]["type"] == "string"
    assert field_ids_array["items"]["minLength"] == 1

    field_types = properties["field_types"]
    field_types_array = next(
        entry for entry in field_types["anyOf"] if entry["type"] == "array"
    )
    assert field_types["default"] is None
    assert field_types_array["minItems"] == 1
    assert field_types_array["items"]["enum"] == ["system", "custom"]

    assert properties["start_at"]["default"] == 0
    assert properties["start_at"]["minimum"] == 0
    assert properties["max_results"]["default"] == 20
    assert properties["max_results"]["minimum"] == 1
    assert properties["raw"]["default"] is False
    assert "pagination metadata" in properties["raw"]["description"].lower()


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
