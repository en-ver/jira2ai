"""Adapter-neutral result contracts for shared Jira operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class OperationResult:
    """Human-readable output plus optional raw data for adapters."""

    text: str
    data: Any | None = None
    raw_content: str | None = None

    @property
    def has_raw_output(self) -> bool:
        """Whether the result can be adapted to a raw/tool response."""
        return self.data is not None or self.raw_content is not None

    @classmethod
    def text_only(cls, text: str) -> OperationResult:
        """Create a text-only result."""
        return cls(text=text)

    @classmethod
    def with_data(
        cls,
        text: str,
        data: Any,
        *,
        raw_content: str | None = None,
    ) -> OperationResult:
        """Create a result with structured data and optional serialized raw content."""
        return cls(text=text, data=data, raw_content=raw_content)


__all__ = ["OperationResult"]
