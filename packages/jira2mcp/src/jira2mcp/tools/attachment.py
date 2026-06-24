"""Download a Jira attachment."""

from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from fastmcp import Context
from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from jira2ai_core.client import get_api
from jira2ai_core.errors import (
    AttachmentDownloadError,
    AttachmentError,
    Jira2AIValidationError,
    JiraOperationError,
)
from jira2ai_core.operations.attachments import (
    download_attachment_content,
    format_attachment_download_result,
    plan_attachment_download,
    validate_attachment_id,
)
from jira2py import JiraAPI

from jira2mcp.adapter import to_tool_error

from .server import tools


def _path_within_roots(resolved_path: Path, roots: list) -> bool:
    """Check if a resolved path is within any of the declared MCP roots."""
    for root in roots:
        uri = str(root.uri) if hasattr(root, "uri") else str(root)
        parsed = urlparse(uri)
        # file:///path -> /path; plain path -> use as-is
        root_path = Path(parsed.path if parsed.scheme == "file" else uri).resolve()
        if resolved_path.is_relative_to(root_path):
            return True
    return False


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def attachment(
    attachment_id: Annotated[str, "Attachment ID (e.g. 63899)"],
    output_path: Annotated[
        str | None,
        "Path to save the attachment. Can be a directory (filename from Jira is used) "
        "or a full file path. Defaults to current directory",
    ] = None,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str:
    """Download a Jira attachment by its ID.

    Use jira_read to get attachment IDs and metadata first.
    The attachment is saved to the specified output path (or current directory).
    """
    try:
        validate_attachment_id(attachment_id)
    except Jira2AIValidationError as exc:
        raise to_tool_error(exc) from exc

    await ctx.info(f"Downloading attachment {attachment_id}")

    try:
        plan = plan_attachment_download(
            attachment_id,
            output_path=output_path,
            api=api,
        )
    except JiraOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except AttachmentError as exc:
        raise to_tool_error(exc) from exc

    roots = []
    try:
        roots = await ctx.list_roots()
    except Exception:
        roots = []

    if roots:
        if not _path_within_roots(plan.resolved_output, roots):
            raise ToolError(
                f"Path is outside allowed MCP roots. Resolved path: {plan.resolved_output}"
            )
    else:
        # Fallback: no roots declared, use CWD as boundary
        cwd = Path.cwd().resolve()
        if not plan.resolved_output.is_relative_to(cwd):
            raise ToolError(
                f"Cannot write outside working directory ({cwd}). "
                f"Resolved path: {plan.resolved_output}"
            )

    try:
        download_attachment_content(plan, api=api)
    except AttachmentDownloadError as exc:
        raise to_tool_error(exc) from exc

    return format_attachment_download_result(plan)
