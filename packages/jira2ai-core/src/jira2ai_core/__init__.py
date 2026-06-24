"""Shared core package for Jira AI integrations."""

from .errors import (
    AttachmentDownloadError,
    AttachmentError,
    AttachmentPathError,
    Jira2AIConfigError,
    Jira2AIError,
    Jira2AIValidationError,
    JiraOperationError,
)
from .results import OperationResult

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "AttachmentDownloadError",
    "AttachmentError",
    "AttachmentPathError",
    "Jira2AIConfigError",
    "Jira2AIError",
    "Jira2AIValidationError",
    "JiraOperationError",
    "OperationResult",
]
