"""Jira attachment tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, cast
from urllib.parse import urlparse

from fastmcp import Context
from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from jira2py import JiraAPI
from jira2py.helpers import HelperResult, JiraHelpers
from jira2py.helpers.errors import (
    AttachmentDownloadError,
    AttachmentError,
    JiraHelperError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)
from jira2py.helpers.models import AttachmentDownloadPlan
from mcp.types import Root

from jira2mcp.adapter import adapt_operation_result, to_tool_error
from jira2mcp.attachment_io import (
    download_attachment_content,
    format_attachment_download_result,
)
from jira2mcp.utils import get_api

from .server import tools


def _validate_attachment_id(*, attachment_id: str, api: JiraAPI) -> None:
    helpers = JiraHelpers(api)
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


async def _plan_download_with_root_checks(
    *,
    attachment_id: str,
    output_path: str | None,
    ctx: Context,
    api: JiraAPI,
) -> AttachmentDownloadPlan:
    helpers = JiraHelpers(api)
    plan_result = helpers.attachments.plan_download(
        attachment_id,
        output_path=output_path,
    )
    plan = cast(AttachmentDownloadPlan, plan_result.data)

    roots: list[Root] | None = None
    try:
        roots = await ctx.list_roots()
    except Exception:
        pass

    if roots:
        if not _path_within_roots(plan.resolved_output, roots):
            raise ToolError(
                f"Path is outside allowed MCP roots. Resolved path: {plan.resolved_output}"
            )
    else:
        cwd = Path.cwd().resolve()
        if not _path_within_cwd(plan.resolved_output):
            raise ToolError(
                f"Cannot write outside working directory ({cwd}). "
                f"Resolved path: {plan.resolved_output}"
            )

    return plan


def _download_result_from_plan(
    *,
    attachment_id: str,
    plan: AttachmentDownloadPlan,
    api: JiraAPI,
) -> HelperResult:
    try:
        download_attachment_content(plan, api=api)
    except AttachmentDownloadError as exc:
        raise to_tool_error(exc) from exc

    return HelperResult.with_data(
        format_attachment_download_result(plan),
        {
            "status": "downloaded",
            "attachment_id": attachment_id,
            "filename": plan.filename,
            "output_file": plan.output_file,
            "size": plan.meta.size,
            "mime_type": plan.meta.mimeType,
            "content_url": plan.content_url,
        },
    )


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
    _validate_attachment_id(attachment_id=attachment_id, api=api)
    await ctx.info(f"Downloading attachment {attachment_id}")

    try:
        plan = await _plan_download_with_root_checks(
            attachment_id=attachment_id,
            output_path=output_path,
            ctx=ctx,
            api=api,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except AttachmentError as exc:
        raise to_tool_error(exc) from exc

    _download_result_from_plan(attachment_id=attachment_id, plan=plan, api=api)
    return format_attachment_download_result(plan)


@tools.tool(
    tags={"read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def download_attachment(
    attachment_id: Annotated[str, "Attachment ID (e.g. 63899)"],
    output_path: Annotated[
        str | None,
        "Path to save the attachment. Can be a directory (filename from Jira is used) "
        "or a full file path. Defaults to current directory",
    ] = None,
    raw: Annotated[
        bool, "Return raw structured output describing the download"
    ] = False,
    ctx: Context = CurrentContext(),
    api: JiraAPI = Depends(get_api),
) -> str | ToolResult:
    """Download a Jira attachment by its ID with optional raw structured output."""
    _validate_attachment_id(attachment_id=attachment_id, api=api)
    await ctx.info(f"Downloading attachment {attachment_id}")

    try:
        plan = await _plan_download_with_root_checks(
            attachment_id=attachment_id,
            output_path=output_path,
            ctx=ctx,
            api=api,
        )
    except JiraHelperOperationError as exc:
        await ctx.error(str(exc))
        raise to_tool_error(exc) from exc
    except AttachmentError as exc:
        raise to_tool_error(exc) from exc

    result = _download_result_from_plan(attachment_id=attachment_id, plan=plan, api=api)
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
    """Upload a local file as a Jira issue attachment."""
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
