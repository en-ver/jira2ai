from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from conftest import FakeContext
from fastmcp.exceptions import ToolError
from jira2mcp.attachment_io import (
    download_attachment_content,
    format_attachment_download_result,
)
from jira2mcp.tools import attachment as attachment_tool
from jira2py.helpers import JiraHelpers
from jira2py.helpers.errors import AttachmentError, JiraHelperOperationError
from jira2py.helpers.models import AttachmentDownloadPlan

ATTACHMENT_META = {
    "id": 7,
    "filename": "debug.log",
    "mimeType": "text/plain",
    "size": 1536,
}


def _plan_download(api, attachment_id: str, *, output_path: str | None = None):
    result = JiraHelpers(api).attachments.plan_download(
        attachment_id,
        output_path=output_path,
    )
    return result.data


def test_plan_attachment_download_builds_metadata_and_destination(
    tmp_path,
    make_attachment_api,
) -> None:
    api = make_attachment_api(metadata_response=ATTACHMENT_META)

    plan = _plan_download(api, "7", output_path=str(tmp_path))

    assert api._get_attachment_metadata.calls == [{"attachment_id": "7"}]
    assert isinstance(plan, AttachmentDownloadPlan)
    assert plan.filename == "debug.log"
    assert plan.output_file == str(tmp_path / "debug.log")
    assert plan.resolved_output == (tmp_path / "debug.log").resolve()
    assert plan.content_url.endswith("/rest/api/3/attachment/content/7")
    assert format_attachment_download_result(plan) == (
        f"Downloaded: debug.log\n"
        f"Type: text/plain\n"
        f"Size: 1.5 KB\n"
        f"Saved to: {tmp_path / 'debug.log'}"
    )


def test_plan_attachment_download_falls_back_when_filename_sanitizes_empty(
    monkeypatch,
    tmp_path,
    make_attachment_api,
) -> None:
    monkeypatch.chdir(tmp_path)
    api = make_attachment_api(
        metadata_response={**ATTACHMENT_META, "filename": " .. /.. "}
    )

    plan = _plan_download(api, "7")

    assert plan.filename == "attachment-7"
    assert plan.output_file == str(tmp_path / "attachment-7")


def test_plan_attachment_download_rejects_too_large_attachments(
    make_attachment_api,
) -> None:
    api = make_attachment_api(
        metadata_response={
            **ATTACHMENT_META,
            "size": (100 * 1024 * 1024) + 1,
        }
    )

    with pytest.raises(
        AttachmentError,
        match=r"Attachment too large: 100\.0 MB\. Max allowed: 100\.0 MB",
    ):
        _plan_download(api, "7")


def test_plan_attachment_download_wraps_metadata_failures(make_attachment_api) -> None:
    api = make_attachment_api(metadata_error=RuntimeError("boom"))

    with pytest.raises(
        JiraHelperOperationError,
        match=r"Failed to fetch attachment metadata 7: boom",
    ):
        _plan_download(api, "7")


def test_download_attachment_content_uses_injected_downloader(
    tmp_path,
    make_attachment_api,
) -> None:
    api = make_attachment_api(metadata_response=ATTACHMENT_META)
    plan = _plan_download(
        api,
        "7",
        output_path=f"{tmp_path / 'downloads'}/",
    )
    calls: list[tuple[str, Path, tuple[str, str]]] = []

    def downloader(url: str, destination: Path, auth: tuple[str, str]) -> None:
        calls.append((url, destination, auth))
        destination.write_bytes(b"hello")

    download_attachment_content(plan, api=api, downloader=downloader)

    assert calls == [
        (
            plan.content_url,
            tmp_path / "downloads" / "debug.log",
            ("user@example.com", "secret-token"),
        )
    ]
    assert (tmp_path / "downloads" / "debug.log").read_bytes() == b"hello"


def test_attachment_tool_rejects_empty_ids_before_logging(fake_ctx) -> None:
    with pytest.raises(
        ToolError, match=r"attachment_id is required and cannot be empty"
    ):
        asyncio.run(
            attachment_tool.attachment(
                "   ",
                ctx=cast(Any, fake_ctx),
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_attachment_tool_logs_metadata_errors(fake_ctx, make_attachment_api) -> None:
    api = make_attachment_api(metadata_error=RuntimeError("boom"))

    with pytest.raises(ToolError, match=r"Failed to fetch attachment metadata 7: boom"):
        asyncio.run(
            attachment_tool.attachment(
                "7",
                ctx=cast(Any, fake_ctx),
                api=api,
            )
        )

    assert fake_ctx.info_messages == ["Downloading attachment 7"]
    assert fake_ctx.error_messages == ["Failed to fetch attachment metadata 7: boom"]


def test_attachment_tool_keeps_root_approval_in_mcp_adapter(
    monkeypatch,
    tmp_path,
    make_attachment_api,
) -> None:
    ctx = FakeContext(roots=[SimpleNamespace(uri=tmp_path.as_uri())])
    api = make_attachment_api(metadata_response=ATTACHMENT_META)
    downloaded_to: list[Path] = []

    def fake_download(plan, *, api) -> None:
        downloaded_to.append(Path(plan.output_file))
        Path(plan.output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(plan.output_file).write_bytes(b"ok")

    monkeypatch.setattr(attachment_tool, "download_attachment_content", fake_download)

    result = asyncio.run(
        attachment_tool.attachment(
            "7",
            output_path=f"{tmp_path / 'downloads'}/",
            ctx=cast(Any, ctx),
            api=api,
        )
    )

    assert downloaded_to == [tmp_path / "downloads" / "debug.log"]
    assert result == (
        f"Downloaded: debug.log\n"
        f"Type: text/plain\n"
        f"Size: 1.5 KB\n"
        f"Saved to: {tmp_path / 'downloads' / 'debug.log'}"
    )


def test_attachment_tool_rejects_paths_outside_mcp_roots(
    monkeypatch,
    tmp_path,
    make_attachment_api,
) -> None:
    ctx = FakeContext(roots=[SimpleNamespace(uri=(tmp_path / "allowed").as_uri())])
    api = make_attachment_api(metadata_response=ATTACHMENT_META)

    def fail_download(*_args, **_kwargs) -> None:
        raise AssertionError("download should not start for rejected paths")

    monkeypatch.setattr(attachment_tool, "download_attachment_content", fail_download)

    with pytest.raises(ToolError, match=r"Path is outside allowed MCP roots"):
        asyncio.run(
            attachment_tool.attachment(
                "7",
                output_path=f"{tmp_path / 'blocked'}/",
                ctx=cast(Any, ctx),
                api=api,
            )
        )


def test_attachment_tool_uses_cwd_boundary_when_no_roots(
    monkeypatch,
    tmp_path,
    make_attachment_api,
) -> None:
    monkeypatch.chdir(tmp_path)
    ctx = FakeContext()
    api = make_attachment_api(metadata_response=ATTACHMENT_META)

    def fail_download(*_args, **_kwargs) -> None:
        raise AssertionError("download should not start for rejected paths")

    monkeypatch.setattr(attachment_tool, "download_attachment_content", fail_download)

    with pytest.raises(ToolError, match=r"Cannot write outside working directory"):
        asyncio.run(
            attachment_tool.attachment(
                "7",
                output_path="../outside.txt",
                ctx=cast(Any, ctx),
                api=api,
            )
        )
