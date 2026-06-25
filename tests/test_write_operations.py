from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2mcp.adf import markdown_to_adf
from jira2mcp.tools.add_link import add_link
from jira2mcp.tools.comment import comment
from jira2mcp.tools.create import create
from jira2mcp.tools.delete_link import delete_link
from jira2mcp.tools.edit import edit
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import JiraHelperValidationError

ADF_FIELDS = [
    {
        "id": "customfield_10001",
        "schema": {
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
        },
    }
]


CREATE_RESPONSE = {
    "id": "10001",
    "key": "PROJ-123",
    "self": "https://example.atlassian.net/rest/api/3/issue/10001",
}


EDIT_RESPONSE = {
    "id": "10001",
    "key": "PROJ-123",
    "fields": {"summary": "Updated summary"},
}


COMMENT_RESPONSE = {
    "id": "20001",
    "body": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Looks good"}],
            }
        ],
    },
}


def test_create_issue_operation_converts_markdown_fields_and_formats_output(
    make_write_api,
) -> None:
    api = make_write_api(
        fields_response=ADF_FIELDS,
        create_response=CREATE_RESPONSE,
    )

    result = JiraHelpers(api).issues.create(
        "PROJ",
        "Bug",
        "Fix thing",
        description="Hello **world**",
        fields={
            "customfield_10001": "Needs _details_",
            "labels": ["backend"],
        },
    )

    assert api._methods["get_fields"].calls == [{}]
    assert api._methods["create_issue"].calls == [
        {
            "fields": {
                "customfield_10001": markdown_to_adf("Needs _details_"),
                "labels": ["backend"],
                "project": {"key": "PROJ"},
                "issuetype": {"name": "Bug"},
                "summary": "Fix thing",
                "description": markdown_to_adf("Hello **world**"),
            }
        }
    ]
    assert result.data == CREATE_RESPONSE
    assert result.text == (
        "Created PROJ-123: Fix thing\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )


def test_create_and_edit_operations_raise_helper_validation_errors() -> None:
    helpers = JiraHelpers(cast(Any, object()))

    with pytest.raises(
        JiraHelperValidationError,
        match=r"Use explicit parameters instead of fields for: project",
    ):
        helpers.issues.create(
            "PROJ",
            "Bug",
            "Fix thing",
            fields={"project": {"key": "OTHER"}},
        )

    with pytest.raises(
        JiraHelperValidationError,
        match=(
            "Nothing to update. Provide at least one of: summary, description, or fields."
        ),
    ):
        helpers.issues.edit("PROJ-123")


def test_edit_issue_operation_sets_return_issue_for_raw_output(make_write_api) -> None:
    api = make_write_api(
        fields_response=ADF_FIELDS,
        edit_response=EDIT_RESPONSE,
    )

    result = JiraHelpers(api).issues.edit(
        "PROJ-123",
        summary="Updated summary",
        fields={"customfield_10001": "Fresh _content_"},
        raw=True,
    )

    assert api._methods["get_fields"].calls == [{}]
    assert api._methods["edit_issue"].calls == [
        {
            "issue_id": "PROJ-123",
            "fields": {
                "customfield_10001": markdown_to_adf("Fresh _content_"),
                "summary": "Updated summary",
            },
            "return_issue": True,
        }
    ]
    assert result.data == EDIT_RESPONSE
    assert result.text == (
        "Successfully updated PROJ-123\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )


def test_comment_and_link_operations_preserve_current_text_and_raw_payloads(
    make_write_api,
) -> None:
    api = make_write_api(comment_response=COMMENT_RESPONSE)
    helpers = JiraHelpers(api)

    comment_result = helpers.comments.add("PROJ-123", "Looks good")
    create_link_result = helpers.links.create("Blocks", "PROJ-1", "PROJ-2")
    delete_link_result = helpers.links.delete("77")

    assert api._methods["add_comment"].calls == [
        {
            "issue_id": "PROJ-123",
            "body": markdown_to_adf("Looks good"),
        }
    ]
    assert api._methods["create_link"].calls == [
        {
            "link_type_name": "Blocks",
            "inward_issue_key": "PROJ-2",
            "outward_issue_key": "PROJ-1",
        }
    ]
    assert api._methods["delete_link"].calls == [{"link_id": "77"}]

    assert comment_result.data == COMMENT_RESPONSE
    assert comment_result.text == (
        "Added comment to PROJ-123\nURL: https://example.atlassian.net/browse/PROJ-123"
    )
    assert create_link_result.data == {
        "status": "created",
        "link_type": "Blocks",
        "outward_issue": "PROJ-1",
        "inward_issue": "PROJ-2",
    }
    assert create_link_result.text == "Created link: PROJ-1 blocks PROJ-2"
    assert delete_link_result.data == {"status": "deleted", "link_id": "77"}
    assert delete_link_result.text == "Deleted issue link 77"


def test_create_tool_uses_helper_adapter_for_raw_output(
    fake_ctx, make_write_api
) -> None:
    api = make_write_api(
        fields_response=ADF_FIELDS,
        create_response=CREATE_RESPONSE,
    )

    result = asyncio.run(
        create(
            "PROJ",
            "Bug",
            "Fix thing",
            description="Hello **world**",
            raw=True,
            ctx=fake_ctx,
            api=api,
        )
    )

    assert fake_ctx.info_messages == ["Creating Bug in PROJ: Fix thing"]
    assert fake_ctx.error_messages == []
    assert isinstance(result, ToolResult)
    assert result.structured_content == CREATE_RESPONSE
    assert cast(Any, result.content[0]).text == json.dumps(
        CREATE_RESPONSE, indent=2, default=str
    )


def test_edit_tool_logs_operation_errors(fake_ctx, make_write_api) -> None:
    api = make_write_api(edit_error=RuntimeError("boom"))

    with pytest.raises(ToolError, match=r"Failed to update issue PROJ-123: boom"):
        asyncio.run(edit("PROJ-123", summary="Updated", ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == ["Updating issue PROJ-123"]
    assert fake_ctx.error_messages == ["Failed to update issue PROJ-123: boom"]


def test_comment_and_link_tools_delegate_to_helpers(fake_ctx, make_write_api) -> None:
    api = make_write_api(comment_response=COMMENT_RESPONSE)

    comment_result = asyncio.run(
        comment("PROJ-123", "Looks good", raw=True, ctx=fake_ctx, api=api)
    )
    add_link_result = asyncio.run(
        add_link("Blocks", "PROJ-1", "PROJ-2", raw=True, ctx=fake_ctx, api=api)
    )
    delete_link_result = asyncio.run(delete_link("77", ctx=fake_ctx, api=api))

    assert fake_ctx.info_messages == [
        "Adding comment to PROJ-123",
        "Creating Blocks link: PROJ-1 -> PROJ-2",
        "Deleting issue link 77",
    ]
    assert fake_ctx.error_messages == []

    assert isinstance(comment_result, ToolResult)
    assert comment_result.structured_content == COMMENT_RESPONSE
    assert cast(Any, comment_result.content[0]).text == json.dumps(
        COMMENT_RESPONSE,
        indent=2,
        default=str,
    )

    assert isinstance(add_link_result, ToolResult)
    assert add_link_result.structured_content == {
        "status": "created",
        "link_type": "Blocks",
        "outward_issue": "PROJ-1",
        "inward_issue": "PROJ-2",
    }
    assert cast(Any, add_link_result.content[0]).text == json.dumps(
        add_link_result.structured_content,
        indent=2,
        default=str,
    )
    assert delete_link_result == "Deleted issue link 77"
