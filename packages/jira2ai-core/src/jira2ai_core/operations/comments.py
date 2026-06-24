"""Issue comment operations."""

from __future__ import annotations

from typing import Literal

from jira2py import JiraAPI

from ..adf import markdown_to_adf
from ..errors import JiraOperationError
from ..formatters import format_comment
from ..models import CommentPage
from ..results import OperationResult


def list_comments(
    issue_key: str,
    *,
    start_at: int = 0,
    max_results: int = 50,
    order_by: Literal["created", "-created"] = "created",
    api: JiraAPI,
) -> OperationResult:
    """List comments on a Jira issue."""
    limit = min(max_results, 100)

    try:
        data = api.comments.get_comments(
            issue_id=issue_key,
            start_at=start_at,
            max_results=limit,
            order_by=order_by,
        )
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to fetch comments for {issue_key}: {exc}"
        ) from exc

    page = CommentPage.model_validate(data)
    actual_start = page.startAt

    if not page.comments:
        if actual_start > 0:
            text = f"No comments at offset {actual_start} (total: {page.total})"
        else:
            text = f"No comments on {issue_key}"
        return OperationResult.with_data(text, data)

    lines: list[str] = []
    if page.total > len(page.comments) or actual_start > 0:
        end = actual_start + len(page.comments)
        lines.append(
            f"Comments on {issue_key}: showing {actual_start + 1}–{end} of {page.total}\n"
        )
    else:
        lines.append(f"Comments on {issue_key}: {page.total} total\n")

    for comment in page.comments:
        lines.append(format_comment(comment))
        lines.append("")

    if actual_start + len(page.comments) < page.total:
        next_start = actual_start + len(page.comments)
        lines.append(
            f"--- More comments available. Use start_at={next_start} to fetch the next page. ---"
        )

    return OperationResult.with_data("\n".join(lines), data)


def add_comment(
    issue_key: str,
    body: str,
    *,
    api: JiraAPI,
) -> OperationResult:
    """Add a comment to a Jira issue."""
    try:
        data = api.comments.add_comment(
            issue_id=issue_key,
            body=markdown_to_adf(body),
        )
    except Exception as exc:
        raise JiraOperationError(
            f"Failed to add comment to {issue_key}: {exc}"
        ) from exc

    return OperationResult.with_data(
        f"Added comment to {issue_key}\nURL: {api.credentials.url}/browse/{issue_key}",
        data,
    )


__all__ = ["add_comment", "list_comments"]
