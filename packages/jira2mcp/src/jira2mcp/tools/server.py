"""Shared FastMCP sub-server instance for all Jira tools."""

from fastmcp import FastMCP

tools = FastMCP("Jira Tools", mask_error_details=True)
