from __future__ import annotations

from jira2mcp.utils import TRUNCATION_SUFFIX, format_date, truncate


def test_truncate_adds_suffix_only_when_needed() -> None:
    assert truncate("abcd", max_chars=4) == "abcd"
    assert truncate("abcdef", max_chars=4) == "abcd" + TRUNCATION_SUFFIX


def test_format_date_handles_empty_and_iso_values() -> None:
    assert format_date(None) == "—"
    assert format_date("2026-01-02T03:04:05.000+0000") == "2026-01-02"
