from __future__ import annotations

from inspect import signature

import jira2mcp.adf as adf
from adf_bridge import AdfConversionError


def test_markdown_to_adf_preserves_compatibility_signature_and_blank_document() -> None:
    assert list(signature(adf.markdown_to_adf).parameters) == ["markdown"]
    assert adf.markdown_to_adf("   ") == {"type": "doc", "version": 1, "content": []}


def test_markdown_to_adf_uses_bridge_without_issue_specific_resolution() -> None:
    assert adf.markdown_to_adf("![Diagram](https://example.com/diagram.png)") == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "external",
                            "url": "https://example.com/diagram.png",
                            "alt": "Diagram",
                        },
                    }
                ],
            }
        ],
    }


def test_detect_adf_field_ids_includes_system_and_custom_textareas() -> None:
    metadata = [
        {
            "id": "customfield_10001",
            "schema": {
                "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
            },
        },
        {
            "id": "customfield_10002",
            "schema": {
                "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textfield"
            },
        },
    ]

    assert adf.detect_adf_field_ids(metadata) == {
        "customfield_10001",
        "description",
        "environment",
    }


def test_convert_markdown_fields_only_converts_known_adf_fields() -> None:
    converted = adf.convert_markdown_fields(
        {"customfield_10001": "Hello **world**", "summary": "Fix thing"},
        {"customfield_10001"},
    )

    assert converted == {
        "customfield_10001": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {
                            "type": "text",
                            "text": "world",
                            "marks": [{"type": "strong"}],
                        },
                    ],
                }
            ],
        },
        "summary": "Fix thing",
    }


def test_adf_to_markdown_keeps_blank_and_readable_media_fallbacks() -> None:
    assert adf.adf_to_markdown({"type": "doc", "version": 1, "content": []}) == "(none)"

    document = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "file",
                            "id": "managed-image",
                            "collection": "",
                            "alt": "Screenshot",
                        },
                    }
                ],
            }
        ],
    }

    assert adf.adf_to_markdown(document) == "Screenshot"


def test_adf_to_markdown_uses_readable_fallback_for_bridge_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        adf,
        "_adf_to_markdown",
        lambda _value: (_ for _ in ()).throw(AdfConversionError("boom")),
    )

    assert (
        adf.adf_to_markdown(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "unsupportedBlock",
                        "content": [{"type": "text", "text": "Readable fallback"}],
                    }
                ],
            }
        )
        == "Readable fallback"
    )


def test_markdown_to_adf_uses_literal_text_fallback_for_bridge_errors(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        adf,
        "_markdown_to_adf",
        lambda _value: (_ for _ in ()).throw(AdfConversionError("boom")),
    )

    assert adf.markdown_to_adf("unsupported **Markdown**") == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "unsupported **Markdown**"}],
            }
        ],
    }
