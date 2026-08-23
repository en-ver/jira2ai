"""Helpers for adapting helper contracts to FastMCP tool responses."""

from __future__ import annotations

import json
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import JiraHelperError

from jira2mcp.utils import truncate


def to_tool_error(error: JiraHelperError) -> ToolError:
    """Convert a helper exception into FastMCP's ToolError."""
    return ToolError(str(error))


def _structured_content_for_mcp(data: Any) -> dict[str, Any] | None:
    """Return MCP-compatible structured content for helper raw data."""
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    return {"data": data}


def to_data_tool_result(
    data: Any,
    *,
    raw_content: str | None = None,
) -> ToolResult:
    """Convert structured data into a FastMCP ToolResult."""
    content = raw_content
    if content is None:
        content = json.dumps(data, separators=(",", ":"), default=str)

    return ToolResult(
        content=content,
        structured_content=_structured_content_for_mcp(data),
    )


def to_tool_result(result: HelperResult) -> ToolResult:
    """Convert a raw-capable helper result into a FastMCP ToolResult."""
    if not result.has_raw_output:
        raise ValueError("HelperResult does not contain raw output")

    content = result.raw_content
    if content is None:
        content = json.dumps(result.data, indent=2, default=str)

    return to_data_tool_result(result.data, raw_content=content)


def adapt_operation_result(
    result: HelperResult,
    *,
    raw: bool = False,
    truncate_text: bool = False,
) -> str | ToolResult:
    """Return the MCP-facing output for a shared helper result."""
    if raw and result.has_raw_output:
        return to_tool_result(result)

    text = result.text
    if truncate_text:
        text = truncate(text)
    return text


__all__ = [
    "adapt_operation_result",
    "to_data_tool_result",
    "to_tool_error",
    "to_tool_result",
]
