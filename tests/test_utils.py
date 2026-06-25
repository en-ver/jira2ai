from __future__ import annotations

from jira2mcp.utils import TRUNCATION_SUFFIX, format_date, format_size, truncate


def test_truncate_adds_suffix_only_when_needed() -> None:
    assert truncate("abcd", max_chars=4) == "abcd"
    assert truncate("abcdef", max_chars=4) == "abcd" + TRUNCATION_SUFFIX


def test_format_size_and_date_cover_current_edge_cases() -> None:
    assert format_size(float("nan")) == "unknown size"
    assert format_size(1536) == "1.5 KB"
    assert format_size(3 * 1024 * 1024 * 1024) == "3.0 GB"
    assert format_date(None) == "—"
    assert format_date("2026-01-02T03:04:05.000+0000") == "2026-01-02"
