"""Adapter-neutral error contracts for shared Jira operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class Jira2AIError(Exception):
    """Base error for shared Jira AI core logic."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})


class Jira2AIValidationError(Jira2AIError):
    """Raised when tool or operation input is invalid."""


class Jira2AIConfigError(Jira2AIError):
    """Raised when required Jira/client configuration is missing or invalid."""


class JiraOperationError(Jira2AIError):
    """Raised when a Jira API operation fails."""


class AttachmentError(Jira2AIError):
    """Base error for attachment-related failures."""


class AttachmentPathError(AttachmentError):
    """Raised when an attachment path is unsafe or outside allowed boundaries."""


class AttachmentDownloadError(AttachmentError):
    """Raised when an attachment download fails."""


__all__ = [
    "AttachmentDownloadError",
    "AttachmentError",
    "AttachmentPathError",
    "Jira2AIConfigError",
    "Jira2AIError",
    "Jira2AIValidationError",
    "JiraOperationError",
]
