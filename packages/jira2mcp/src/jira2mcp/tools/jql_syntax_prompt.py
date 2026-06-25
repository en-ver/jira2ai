"""MCP prompt providing JQL syntax reference for building search queries."""

from jira2mcp.jql import JQL_REFERENCE

from .server import tools


@tools.prompt
def jql_syntax() -> str:
    """JQL (Jira Query Language) syntax reference for building search queries.

    Use this prompt to look up JQL fields, operators, functions,
    and query patterns before constructing jira_search queries.
    """
    return JQL_REFERENCE
