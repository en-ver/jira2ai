"""Download a Jira attachment."""

import os
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastmcp import Context
from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.exceptions import ToolError
from jira2py import JiraAPI
from pathvalidate import sanitize_filename

from ..models import AttachmentMeta
from ..utils import format_size, get_api
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
    MAX_DOWNLOAD = 100 * 1024 * 1024  # 100 MB

    if not attachment_id.strip():
        raise ToolError("attachment_id is required and cannot be empty")

    await ctx.info(f"Downloading attachment {attachment_id}")

    # Get metadata
    try:
        meta = AttachmentMeta.model_validate(
            api.attachments.get_attachment_metadata(attachment_id=attachment_id)
        )
    except Exception as e:
        await ctx.error(f"Failed to fetch attachment metadata {attachment_id}: {e}")
        raise ToolError(
            f"Failed to fetch attachment metadata {attachment_id}: {e}"
        ) from e

    raw_filename = os.path.basename(meta.filename or f"attachment-{attachment_id}")
    filename = str(sanitize_filename(raw_filename, platform="universal")).strip()
    if not filename or filename in (".", ".."):
        filename = f"attachment-{attachment_id}"

    if meta.size > MAX_DOWNLOAD:
        raise ToolError(
            f"Attachment too large: {format_size(meta.size)}. "
            f"Max allowed: {format_size(MAX_DOWNLOAD)}"
        )

    # Determine output file path
    if output_path:
        resolved = os.path.abspath(output_path)
        if os.path.isdir(resolved) or output_path.endswith("/"):
            output_file = os.path.join(resolved, filename)
        else:
            output_file = resolved
    else:
        output_file = os.path.abspath(filename)

    # Prevent writing outside allowed boundaries
    resolved_output = Path(output_file).resolve()
    roots = []
    try:
        roots = await ctx.list_roots()
    except Exception:
        roots = []

    if roots:
        if not _path_within_roots(resolved_output, roots):
            raise ToolError(
                f"Path is outside allowed MCP roots. Resolved path: {resolved_output}"
            )
    else:
        # Fallback: no roots declared, use CWD as boundary
        cwd = Path.cwd().resolve()
        if not resolved_output.is_relative_to(cwd):
            raise ToolError(
                f"Cannot write outside working directory ({cwd}). "
                f"Resolved path: {resolved_output}"
            )

    # Download content via streaming
    content_url = f"{api.credentials.url}/rest/api/3/attachment/content/{attachment_id}"
    auth = (api.credentials.username or "", api.credentials.api_token or "")
    timeout = httpx.Timeout(120.0, connect=30.0)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with httpx.Client(http2=True, timeout=timeout) as http_client:
        with http_client.stream(
            "GET",
            content_url,
            auth=auth,
            follow_redirects=True,
        ) as resp:
            resp.raise_for_status()
            with open(output_file, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)

    return (
        f"Downloaded: {filename}\n"
        f"Type: {meta.mimeType}\n"
        f"Size: {format_size(meta.size)}\n"
        f"Saved to: {output_file}"
    )
