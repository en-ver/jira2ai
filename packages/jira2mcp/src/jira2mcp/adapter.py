"""Helpers for adapting core contracts to FastMCP tool responses."""

from __future__ import annotations

import json

from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2ai_core.errors import Jira2AIError
from jira2ai_core.results import OperationResult
from jira2ai_core.utils import truncate


def to_tool_error(error: Jira2AIError) -> ToolError:
    """Convert a core exception into FastMCP's ToolError."""
    return ToolError(str(error))


def to_tool_result(result: OperationResult) -> ToolResult:
    """Convert a raw-capable operation result into a FastMCP ToolResult."""
    if not result.has_raw_output:
        raise ValueError("OperationResult does not contain raw output")

    content = result.raw_content
    if content is None:
        content = json.dumps(result.data, indent=2, default=str)

    return ToolResult(content=content, structured_content=result.data)


def adapt_operation_result(
    result: OperationResult,
    *,
    raw: bool = False,
    truncate_text: bool = False,
) -> str | ToolResult:
    """Return the MCP-facing output for a shared operation result."""
    if raw and result.has_raw_output:
        return to_tool_result(result)

    text = result.text
    if truncate_text:
        text = truncate(text)
    return text


__all__ = ["adapt_operation_result", "to_tool_error", "to_tool_result"]
