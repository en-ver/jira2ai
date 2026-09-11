"""Jira attachment tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from fastmcp import Context
from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.tools import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import (
    JiraHelperError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)
from mcp.types import Root

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.utils import get_api

from .server import tools


def _validate_attachment_id(*, attachment_id: str, helpers: JiraHelpers) -> None:
    try:
        helpers.attachments.validate_id(attachment_id)
    except JiraHelperValidationError as exc:
        raise to_tool_error(exc) from exc


def _path_within_roots(resolved_path: Path, roots: list[Root]) -> bool:
    """Check if a resolved path is within any of the declared MCP roots."""
    for root in roots:
        uri = str(root.uri)
        parsed = urlparse(uri)
        root_path = Path(parsed.path if parsed.scheme == "file" else uri).resolve()
        if resolved_path.is_relative_to(root_path):
            return True
    return False


def _path_within_cwd(resolved_path: Path) -> bool:
    """Check if a resolved path is within the server working directory."""
    return resolved_path.is_relative_to(Path.cwd().resolve())


def _validate_upload_path(file_path: str) -> None:
    """Reject upload paths that escape the server working directory."""
    resolved_path = Path(file_path).expanduser().resolve(strict=False)
    if not _path_within_cwd(resolved_path):
        raise ToolError(
            "Attachment upload path must stay within the server working directory: "
            f"{file_path}"
        )


async def _resolve_download_directory(*, directory: str, ctx: Context) -> Path:
    """Resolve and authorize a download directory without owning filename policy."""
    resolved = Path(directory).expanduser().resolve(strict=False)

    try:
        roots = await ctx.list_roots()
    except Exception:
        roots = None

    if roots:
        if not _path_within_roots(resolved, roots):
            raise ToolError(
                "Directory is outside allowed MCP roots. "
                f"Resolved directory: {resolved}"
            )
    elif not _path_within_cwd(resolved):
        cwd = Path.cwd().resolve()
        raise ToolError(
            f"Cannot write outside working directory ({cwd}). "
            f"Resolved directory: {resolved}"
        )

    return resolved


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def attachments(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """List attachments on a Jira issue."""
    await ctx.info(f"Fetching attachments for {issue_key}")

    try:
        result = JiraHelpers(api).attachments.list(issue_key)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def attachment_metadata(
    attachment_id: Annotated[str, "Attachment ID (e.g. 63899)"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Read metadata for a Jira attachment by ID."""
    await ctx.info(f"Fetching attachment metadata {attachment_id}")

    try:
        result = JiraHelpers(api).attachments.read(attachment_id)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def download_attachment(
    attachment_id: Annotated[str, "Attachment ID (e.g. 63899)"],
    directory: Annotated[
        str,
        "Directory in which to save the attachment. Relative paths are resolved from "
        "the server working directory",
    ] = ".",
    filename: Annotated[
        str | None,
        "Optional single destination filename, not a path. Defaults to the sanitized "
        "Jira filename",
    ] = None,
    raw: Annotated[bool, "Return structured output describing the download"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Download a Jira attachment into an authorized directory."""
    helpers = JiraHelpers(api)
    _validate_attachment_id(attachment_id=attachment_id, helpers=helpers)
    await ctx.info(f"Downloading attachment {attachment_id}")

    try:
        resolved_directory = await _resolve_download_directory(
            directory=directory,
            ctx=ctx,
        )
        result = helpers.attachments.download(
            attachment_id,
            directory=resolved_directory,
            filename=filename,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def upload_attachment(
    issue_key: Annotated[str, "Issue key (e.g. PROJ-123)"],
    file_path: Annotated[str, "Local file path to upload"],
    raw: Annotated[bool, "Return raw JSON from the API"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Upload a local file as a Jira issue attachment.

    With raw=True, each uploaded item's existing content field is available at
    structuredContent.data[0].content for Markdown image writes to this issue.
    """
    _validate_upload_path(file_path)
    await ctx.info(f"Uploading attachment to {issue_key}: {file_path}")

    try:
        result = JiraHelpers(api).attachments.upload(issue_key, file_path)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw, truncate_text=True)


@tools.tool(
    tags={"write"},
    annotations={
        "readOnlyHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def delete_attachment(
    attachment_id: Annotated[str, "Attachment ID (e.g. 63899)"],
    raw: Annotated[bool, "Return raw helper result"] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Delete a Jira attachment by explicit attachment ID."""
    await ctx.info(f"Deleting attachment {attachment_id}")

    try:
        result = JiraHelpers(api).attachments.delete(attachment_id)
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except JiraHelperError as exc:
        raise to_tool_error(exc) from exc

    return adapt_operation_result(result, raw=raw)
