from __future__ import annotations

import jira2ai_core.adf as core_adf
import jira2ai_core.client as core_client
import jira2ai_core.formatters as core_formatters
import jira2ai_core.models as core_models
import jira2ai_core.utils as core_utils
import jira2mcp.adf as mcp_adf
import jira2mcp.formatters as mcp_formatters
import jira2mcp.models as mcp_models
import jira2mcp.utils as mcp_utils


def test_jira2mcp_helper_modules_are_core_shims() -> None:
    assert mcp_adf.adf_to_markdown is core_adf.adf_to_markdown
    assert mcp_formatters.format_issue_full is core_formatters.format_issue_full
    assert mcp_models.JiraIssue is core_models.JiraIssue
    assert mcp_utils.truncate is core_utils.truncate
    assert mcp_utils.get_api is core_client.get_api
