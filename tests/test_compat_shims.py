from __future__ import annotations

import jira2mcp.adf as mcp_adf
import jira2mcp.formatters as mcp_formatters
import jira2mcp.models as mcp_models
import jira2mcp.utils as mcp_utils
from jira2py.helpers.issues import DEFAULT_FIELDS
from jira2py.helpers.models import FieldMeta, FieldSchema, JiraIssue


def test_jira2mcp_helper_modules_expose_runtime_local_or_public_helpers() -> None:
    assert mcp_models.JiraIssue is JiraIssue
    assert mcp_models.FieldMeta is FieldMeta
    assert mcp_models.FieldSchema is FieldSchema
    assert mcp_formatters.DEFAULT_FIELDS == DEFAULT_FIELDS
    assert mcp_adf.adf_to_markdown.__module__ == "jira2mcp.adf"
    assert mcp_utils.truncate("abcdef", max_chars=4).endswith(
        mcp_utils.TRUNCATION_SUFFIX
    )
    assert mcp_utils.get_api.__module__ == "jira2mcp.utils"
