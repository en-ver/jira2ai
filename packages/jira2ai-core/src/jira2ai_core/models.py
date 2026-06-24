"""Pydantic models for Jira API responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JiraModel(BaseModel):
    """Base model — allows extra fields so unknown API data passes through."""

    model_config = ConfigDict(extra="allow")


# --- Primitives ---


class NamedResource(JiraModel):
    """A Jira resource with a name (status, issuetype, priority, component, version)."""

    name: str = "—"


class JiraUser(JiraModel):
    """A Jira user."""

    displayName: str = "Unknown"
    accountId: str = "?"
    active: bool = True


class IssueRef(JiraModel):
    """Minimal issue reference (e.g. parent link)."""

    key: str = "?"


# --- Attachments ---


class AttachmentMeta(JiraModel):
    """Attachment metadata."""

    id: int = 0
    filename: str = ""
    mimeType: str = "application/octet-stream"
    size: int = 0


# --- Comments ---


class JiraComment(JiraModel):
    """A single Jira comment."""

    author: JiraUser | None = None
    created: str | None = None
    updated: str | None = None
    body: dict[str, Any] | None = None


class CommentPage(JiraModel):
    """Paginated list of comments."""

    comments: list[JiraComment] = []
    total: int = 0
    startAt: int = 0


# --- Subtasks & Issue Links ---


class SubtaskFields(JiraModel):
    """Fields included in a subtask reference."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None


class Subtask(JiraModel):
    """A subtask reference within a parent issue."""

    key: str = "?"
    fields: SubtaskFields = Field(default_factory=SubtaskFields)


class IssueLinkType(JiraModel):
    """Type descriptor for an issue link."""

    name: str = "?"
    inward: str = "?"
    outward: str = "?"


class LinkedIssueFields(JiraModel):
    """Fields included in a linked issue reference."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None


class LinkedIssue(JiraModel):
    """A linked issue reference (inward or outward side)."""

    key: str = "?"
    fields: LinkedIssueFields = Field(default_factory=LinkedIssueFields)


class IssueLink(JiraModel):
    """A link between two issues."""

    id: str = ""
    type: IssueLinkType = Field(default_factory=IssueLinkType)
    inwardIssue: LinkedIssue | None = None
    outwardIssue: LinkedIssue | None = None


# --- Issues ---


class IssueFields(JiraModel):
    """Fields of a Jira issue."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None
    priority: NamedResource | None = None
    assignee: JiraUser | None = None
    reporter: JiraUser | None = None
    created: str | None = None
    updated: str | None = None
    labels: list[str] = []
    components: list[NamedResource] = []
    fixVersions: list[NamedResource] = []
    description: dict[str, Any] | None = None
    comment: CommentPage | None = None
    attachment: list[AttachmentMeta] = []
    subtasks: list[Subtask] = []
    issuelinks: list[IssueLink] = []


class JiraIssue(JiraModel):
    """A Jira issue."""

    key: str = "?"
    fields: IssueFields = Field(default_factory=IssueFields)


class SearchResult(JiraModel):
    """Response from enhanced search."""

    issues: list[JiraIssue] = []
    nextPageToken: str | None = None
    total: int | None = None
    isLast: bool | None = None


# --- Projects ---


class JiraProject(JiraModel):
    """A Jira project."""

    key: str = "?"
    name: str = "?"


class ProjectSearchResult(JiraModel):
    """Response from project search."""

    values: list[JiraProject] = []
    isLast: bool = True
    total: int | None = None


# --- Field metadata ---


class IssueType(JiraModel):
    """A Jira issue type."""

    id: str = "?"
    name: str = "?"
    subtask: bool = False


class FieldSchema(JiraModel):
    """Schema info for a field."""

    type: str = "unknown"
    custom: str = ""


class FieldMeta(JiraModel):
    """Metadata for a single field on create/edit screen."""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    fieldId: str = ""
    key: str = ""
    id: str = ""
    name: str = "?"
    required: bool = False
    jira_schema: FieldSchema | None = Field(default=None, validation_alias="schema")
    allowedValues: list[Any] = []
    defaultValue: Any = None

    @property
    def resolved_id(self) -> str:
        """Best available field identifier."""
        return self.fieldId or self.key or self.id or "?"


# --- Helpers ---


def user_display(user: JiraUser | None) -> str:
    """Display name for a user, or 'Unassigned' if None."""
    return user.displayName if user else "Unassigned"
