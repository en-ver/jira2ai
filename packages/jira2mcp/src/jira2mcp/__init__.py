"""Jira MCP Server — Model Context Protocol server for Jira Cloud."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from importlib.metadata import version as _pkg_version

from fastmcp import FastMCP

from .tools import tools
from .utils import set_credentials_file

mcp = FastMCP(
    "jira2mcp",
    version=_pkg_version("jira2mcp"),
    instructions=(
        "Jira Cloud integration server. All tools are prefixed with 'jira_'.\n"
        "Key workflows:\n"
        "- Before creating: use jira_fields with project_key + issue_type to discover required fields\n"
        "- Use jira_list_fields for one server-paged field catalog; its project context does not determine issue-type or screen applicability\n"
        "- Before assigning: use jira_users to look up account IDs\n"
        "- Descriptions and comments accept markdown (auto-converted to ADF)\n"
        "- jira_read requires a non-empty fields array; request only the Jira fields needed\n"
        "- Use jira_comments for comments, jira_changelogs for complete issue history, jira_changelogs_by_ids for known changelog IDs, jira_issue_links for link IDs, and jira_attachments or jira_attachment_metadata for attachment metadata\n"
        "- jira_changelogs fetches every GET page before applying optional local timestamp and fieldId filters; result pagination is local\n"
        "- Read the data://jira/link-types resource before creating issue links\n"
        "- Use the jql_syntax prompt for JQL syntax reference when building search queries"
    ),
    mask_error_details=True,
    on_duplicate="error",
)
mcp.mount(tools, namespace="jira")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jira2mcp",
        description="Jira Cloud MCP server",
    )
    parser.add_argument(
        "--credentials-file",
        metavar="PATH",
        help="Explicit path to a Jira Cloud JSON credentials file",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the MCP server."""
    args = _build_arg_parser().parse_args(argv)
    set_credentials_file(args.credentials_file)
    mcp.run(transport="stdio")
