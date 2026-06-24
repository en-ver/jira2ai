"""User metadata operations."""

from __future__ import annotations

from jira2py import JiraAPI

from ..errors import JiraOperationError
from ..models import JiraUser
from ..results import OperationResult


def search_users(
    query: str,
    *,
    max_results: int = 10,
    api: JiraAPI,
) -> OperationResult:
    """Search Jira users by name or email."""
    limit = min(max_results, 50)

    try:
        data = api.users.search_users(query=query, max_results=limit)
    except Exception as exc:
        raise JiraOperationError(f"Failed to search users: {exc}") from exc

    user_list = [JiraUser.model_validate(user) for user in data]

    if not user_list:
        return OperationResult.with_data(f"No users found matching: {query}", data)

    lines = [f"Found {len(user_list)} user(s):\n"]
    for user in user_list:
        status = " (inactive)" if not user.active else ""
        lines.append(f"- {user.displayName}{status} — accountId: {user.accountId}")

    return OperationResult.with_data("\n".join(lines), data)


__all__ = ["search_users"]
