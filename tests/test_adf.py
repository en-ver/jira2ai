from __future__ import annotations

import jira2mcp.adf as adf


def test_markdown_to_adf_returns_empty_doc_for_blank_input() -> None:
    assert adf.markdown_to_adf("   ") == {"type": "doc", "version": 1, "content": []}


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


def test_adf_to_markdown_falls_back_to_plain_text_extraction(
    monkeypatch,
) -> None:
    class BrokenDocument:
        def __init__(self, _value) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(adf, "Document", BrokenDocument)

    value = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Top"},
                    {"type": "text", "text": "level"},
                ],
            },
            {
                "type": "nestedExpand",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Nested text"}],
                    }
                ],
            },
        ],
    }

    assert adf.adf_to_markdown(value) == "Top level Nested text"
