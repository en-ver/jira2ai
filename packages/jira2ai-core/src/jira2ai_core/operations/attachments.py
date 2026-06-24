"""Attachment operations."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
from jira2py import JiraAPI
from pathvalidate import sanitize_filename

from ..errors import (
    AttachmentDownloadError,
    AttachmentError,
    Jira2AIValidationError,
    JiraOperationError,
)
from ..models import AttachmentMeta
from ..utils import format_size

DEFAULT_MAX_DOWNLOAD = 100 * 1024 * 1024  # 100 MB
_ATTACHMENT_CHUNK_SIZE = 65536
_ATTACHMENT_TIMEOUT = httpx.Timeout(120.0, connect=30.0)
AttachmentDownloader = Callable[[str, Path, tuple[str, str]], None]


@dataclass(slots=True, frozen=True)
class AttachmentDownloadPlan:
    """Download metadata plus the planned destination path."""

    attachment_id: str
    filename: str
    output_file: str
    resolved_output: Path
    meta: AttachmentMeta
    content_url: str


def validate_attachment_id(attachment_id: str) -> None:
    """Validate attachment id input before adapter logging."""
    if not attachment_id.strip():
        raise Jira2AIValidationError("attachment_id is required and cannot be empty")


def plan_attachment_download(
    attachment_id: str,
    *,
    output_path: str | None = None,
    api: JiraAPI,
    max_download: int = DEFAULT_MAX_DOWNLOAD,
) -> AttachmentDownloadPlan:
    """Fetch attachment metadata and compute the destination path."""
    validate_attachment_id(attachment_id)

    try:
        meta = AttachmentMeta.model_validate(
            api.attachments.get_attachment_metadata(attachment_id=attachment_id)
        )
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to fetch attachment metadata {attachment_id}: {exc}"
        ) from exc

    filename = sanitize_attachment_filename(meta.filename, attachment_id)
    if meta.size > max_download:
        raise AttachmentError(
            f"Attachment too large: {format_size(meta.size)}. "
            f"Max allowed: {format_size(max_download)}"
        )

    output_file, resolved_output = build_attachment_output_path(
        filename,
        output_path=output_path,
    )
    return AttachmentDownloadPlan(
        attachment_id=attachment_id,
        filename=filename,
        output_file=output_file,
        resolved_output=resolved_output,
        meta=meta,
        content_url=(
            f"{api.credentials.url}/rest/api/3/attachment/content/{attachment_id}"
        ),
    )


def sanitize_attachment_filename(filename: str | None, attachment_id: str) -> str:
    """Sanitize the Jira-provided filename and apply fallback naming."""
    raw_filename = os.path.basename(filename or f"attachment-{attachment_id}")
    sanitized = str(sanitize_filename(raw_filename, platform="universal")).strip()
    if not sanitized or sanitized in (".", ".."):
        return f"attachment-{attachment_id}"
    return sanitized


def build_attachment_output_path(
    filename: str,
    *,
    output_path: str | None = None,
) -> tuple[str, Path]:
    """Plan the output path without applying interface-specific root policy."""
    if output_path:
        resolved = os.path.abspath(output_path)
        if os.path.isdir(resolved) or output_path.endswith("/"):
            output_file = os.path.join(resolved, filename)
        else:
            output_file = resolved
    else:
        output_file = os.path.abspath(filename)

    return output_file, Path(output_file).resolve()


def download_attachment_content(
    plan: AttachmentDownloadPlan,
    *,
    api: JiraAPI,
    downloader: AttachmentDownloader | None = None,
) -> None:
    """Download the attachment content to the planned destination."""
    auth = (api.credentials.username or "", api.credentials.api_token or "")

    try:
        os.makedirs(os.path.dirname(plan.output_file) or ".", exist_ok=True)
        if downloader is None:
            _stream_attachment_to_file(plan.content_url, Path(plan.output_file), auth)
        else:
            downloader(plan.content_url, Path(plan.output_file), auth)
    except Exception as exc:
        raise AttachmentDownloadError(
            f"Failed to download attachment {plan.attachment_id}: {exc}"
        ) from exc


def format_attachment_download_result(plan: AttachmentDownloadPlan) -> str:
    """Build the user-facing success message for an attachment download."""
    return (
        f"Downloaded: {plan.filename}\n"
        f"Type: {plan.meta.mimeType}\n"
        f"Size: {format_size(plan.meta.size)}\n"
        f"Saved to: {plan.output_file}"
    )


def _stream_attachment_to_file(
    content_url: str,
    output_file: Path,
    auth: tuple[str, str],
) -> None:
    with httpx.Client(http2=True, timeout=_ATTACHMENT_TIMEOUT) as http_client:
        with http_client.stream(
            "GET",
            content_url,
            auth=auth,
            follow_redirects=True,
        ) as resp:
            resp.raise_for_status()
            with output_file.open("wb") as file_handle:
                for chunk in resp.iter_bytes(chunk_size=_ATTACHMENT_CHUNK_SIZE):
                    file_handle.write(chunk)


__all__ = [
    "AttachmentDownloadPlan",
    "DEFAULT_MAX_DOWNLOAD",
    "build_attachment_output_path",
    "download_attachment_content",
    "format_attachment_download_result",
    "plan_attachment_download",
    "sanitize_attachment_filename",
    "validate_attachment_id",
]
