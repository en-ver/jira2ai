"""Attachment download helpers for jira2cli."""

from __future__ import annotations

import math
import os
from collections.abc import Callable
from pathlib import Path

import httpx
from jira2py import JiraAPI
from jira2py.helpers.errors import AttachmentDownloadError
from jira2py.helpers.models import AttachmentDownloadPlan

_ATTACHMENT_CHUNK_SIZE = 65536
_ATTACHMENT_TIMEOUT = httpx.Timeout(120.0, connect=30.0)
AttachmentDownloader = Callable[[str, Path, tuple[str, str]], None]


def download_attachment_content(
    plan: AttachmentDownloadPlan,
    *,
    api: JiraAPI,
    downloader: AttachmentDownloader | None = None,
) -> None:
    """Download an attachment to the planned destination."""
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
    """Build the user-facing attachment download success message."""
    return (
        f"Downloaded: {plan.filename}\n"
        f"Type: {plan.meta.mimeType}\n"
        f"Size: {_format_size(plan.meta.size)}\n"
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
        ) as response:
            response.raise_for_status()
            with output_file.open("wb") as file_handle:
                for chunk in response.iter_bytes(chunk_size=_ATTACHMENT_CHUNK_SIZE):
                    file_handle.write(chunk)


def _format_size(size: int | float) -> str:
    if (
        not isinstance(size, (int, float))
        or math.isnan(size)
        or not math.isfinite(size)
        or size < 0
    ):
        return "unknown size"
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{int(size)} bytes"


__all__ = ["download_attachment_content", "format_attachment_download_result"]
