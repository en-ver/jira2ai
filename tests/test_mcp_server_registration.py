from __future__ import annotations

import asyncio

from jira2mcp import mcp

EXPECTED_JIRA_TOOLS = {
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
}


def test_mcp_registers_existing_and_new_jira_tools() -> None:
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}

    assert EXPECTED_JIRA_TOOLS <= names
