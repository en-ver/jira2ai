from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from conftest import FakeContext, RecordingMethod
from fastmcp.exceptions import ToolError
from fastmcp.tools import ToolResult
from jira2mcp.tools import attachment as attachment_tool
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError


def _patch_attachment_helpers(
    monkeypatch: pytest.MonkeyPatch,
    attachments: object,
) -> None:
    monkeypatch.setattr(
        attachment_tool,
        "JiraHelpers",
        lambda _api: SimpleNamespace(attachments=attachments),
    )


def test_download_attachment_rejects_empty_ids_before_logging_or_roots(
    monkeypatch: pytest.MonkeyPatch,
    fake_ctx,
) -> None:
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: (_ for _ in ()).throw(
                JiraHelperValidationError(
                    "attachment_id is required and cannot be empty"
                )
            )
        ),
    )

    with pytest.raises(
        ToolError, match=r"attachment_id is required and cannot be empty"
    ):
        asyncio.run(
            attachment_tool.download_attachment(
                "   ",
                ctx=cast(Any, fake_ctx),
                api=cast(Any, object()),
            )
        )

    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_download_attachment_authorizes_directory_and_delegates_to_core(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    ctx = FakeContext(roots=[SimpleNamespace(uri=tmp_path.as_uri())])
    calls: list[tuple[str, object]] = []
    result = HelperResult.with_data(
        "downloaded",
        {
            "status": "downloaded",
            "attachment_id": "7",
            "filename": "renamed.log",
            "output_file": str(tmp_path / "downloads" / "renamed.log"),
            "size": 5,
            "mime_type": "text/plain",
        },
    )
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda attachment_id: calls.append(("validate", attachment_id)),
            download=lambda attachment_id, *, directory, filename: (
                calls.append(("download", (attachment_id, directory, filename)))
                or result
            ),
        ),
    )

    actual = asyncio.run(
        attachment_tool.download_attachment(
            "7",
            directory="downloads",
            filename="renamed.log",
            ctx=cast(Any, ctx),
            api=cast(Any, object()),
        )
    )

    assert actual == "downloaded"
    assert calls == [
        ("validate", "7"),
        ("download", ("7", (tmp_path / "downloads").resolve(), "renamed.log")),
    ]
    assert ctx.info_messages == ["Downloading attachment 7"]


def test_download_attachment_rejects_directory_outside_advertised_roots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ctx = FakeContext(roots=[SimpleNamespace(uri=(tmp_path / "allowed").as_uri())])

    def download(*_args, **_kwargs) -> None:
        pytest.fail("download must not run")

    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(validate_id=lambda _attachment_id: None, download=download),
    )

    with pytest.raises(ToolError, match=r"Directory is outside allowed MCP roots"):
        asyncio.run(
            attachment_tool.download_attachment(
                "7",
                directory=str(tmp_path / "blocked"),
                ctx=cast(Any, ctx),
                api=cast(Any, object()),
            )
        )


def test_download_attachment_uses_cwd_when_roots_are_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    calls: list[Path] = []
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: None,
            download=lambda _attachment_id, *, directory, filename: (
                calls.append(directory) or HelperResult.text_only("downloaded")
            ),
        ),
    )

    result = asyncio.run(
        attachment_tool.download_attachment(
            "7",
            directory="downloads",
            ctx=cast(Any, FakeContext()),
            api=cast(Any, object()),
        )
    )

    assert result == "downloaded"
    assert calls == [(tmp_path / "downloads").resolve()]


def test_download_attachment_uses_cwd_when_root_lookup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: None,
            download=lambda _attachment_id, *, directory, filename: (
                HelperResult.text_only(str(directory))
            ),
        ),
    )

    result = asyncio.run(
        attachment_tool.download_attachment(
            "7",
            directory="downloads",
            ctx=cast(Any, FakeContext(list_roots_error=RuntimeError("unavailable"))),
            api=cast(Any, object()),
        )
    )

    assert result == str((tmp_path / "downloads").resolve())


def test_download_attachment_rejects_directory_outside_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: None,
            download=lambda *_args, **_kwargs: pytest.fail("download must not run"),
        ),
    )

    with pytest.raises(ToolError, match=r"Cannot write outside working directory"):
        asyncio.run(
            attachment_tool.download_attachment(
                "7",
                directory="../outside",
                ctx=cast(Any, FakeContext()),
                api=cast(Any, object()),
            )
        )


def test_download_attachment_raw_preserves_core_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    data = {
        "status": "downloaded",
        "attachment_id": "7",
        "filename": "debug.log",
        "output_file": str(tmp_path / "debug.log"),
        "size": 5,
        "mime_type": "text/plain",
    }
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: None,
            download=lambda *_args, **_kwargs: HelperResult.with_data(
                "downloaded", data
            ),
        ),
    )

    result = asyncio.run(
        attachment_tool.download_attachment(
            "7",
            raw=True,
            ctx=cast(Any, FakeContext()),
            api=cast(Any, object()),
        )
    )

    assert isinstance(result, ToolResult)
    assert result.structured_content == data


def test_download_attachment_logs_operation_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    ctx = FakeContext()
    _patch_attachment_helpers(
        monkeypatch,
        SimpleNamespace(
            validate_id=lambda _attachment_id: None,
            download=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                JiraHelperOperationError("download failed")
            ),
        ),
    )

    with pytest.raises(ToolError, match="download failed"):
        asyncio.run(
            attachment_tool.download_attachment(
                "7",
                ctx=cast(Any, ctx),
                api=cast(Any, object()),
            )
        )

    assert ctx.info_messages == ["Downloading attachment 7"]
    assert ctx.error_messages == ["download failed"]


def test_upload_attachment_rejects_path_outside_cwd_before_reading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_ctx,
) -> None:
    monkeypatch.chdir(tmp_path)
    add_attachment = RecordingMethod(response=[])
    api = SimpleNamespace(attachments=SimpleNamespace(add_attachment=add_attachment))

    with pytest.raises(
        ToolError,
        match=r"Attachment upload path must stay within the server working directory: ../secret\.txt",
    ):
        asyncio.run(
            attachment_tool.upload_attachment(
                "PROJ-1",
                "../secret.txt",
                ctx=cast(Any, fake_ctx),
                api=cast(Any, api),
            )
        )

    assert add_attachment.calls == []
    assert fake_ctx.info_messages == []
    assert fake_ctx.error_messages == []


def test_upload_attachment_allows_relative_file_within_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_ctx,
) -> None:
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello")
    add_attachment = RecordingMethod(
        response=[
            {
                "id": "7",
                "filename": "notes.txt",
                "mimeType": "text/plain",
                "size": 5,
            }
        ]
    )
    api = SimpleNamespace(attachments=SimpleNamespace(add_attachment=add_attachment))

    result = asyncio.run(
        attachment_tool.upload_attachment(
            "PROJ-1",
            "notes.txt",
            ctx=cast(Any, fake_ctx),
            api=cast(Any, api),
        )
    )

    assert result == (
        "Uploaded attachment to PROJ-1: notes.txt\n"
        "Attachment ID: 7\n"
        "Type: text/plain\n"
        "Size: 5 bytes"
    )
    assert add_attachment.calls == [
        {
            "issue_id": "PROJ-1",
            "filename": "notes.txt",
            "content": b"hello",
            "content_type": "text/plain",
        }
    ]
    assert fake_ctx.info_messages == ["Uploading attachment to PROJ-1: notes.txt"]
    assert fake_ctx.error_messages == []
