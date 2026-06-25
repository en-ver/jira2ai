from hashlib import sha256

from jira2cli.jql import JQL_REFERENCE as CLI_JQL_REFERENCE
from jira2mcp.jql import JQL_REFERENCE as MCP_JQL_REFERENCE
from jira2mcp.tools.jql_syntax_prompt import jql_syntax

EXPECTED_JQL_REFERENCE_SHA256 = (
    "4b12f0a64c08ad6bd45a0db519613d7c0e4950daab52fb3d755535238dbabf26"
)


def test_jql_reference_is_shared_across_runtime_wrappers() -> None:
    assert CLI_JQL_REFERENCE == MCP_JQL_REFERENCE


def test_jql_syntax_prompt_output_is_unchanged() -> None:
    prompt = jql_syntax()

    assert prompt == MCP_JQL_REFERENCE
    assert sha256(prompt.encode()).hexdigest() == EXPECTED_JQL_REFERENCE_SHA256
