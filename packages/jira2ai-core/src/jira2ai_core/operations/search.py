"""Issue search operations."""

from __future__ import annotations

from jira2py import JiraAPI

from ..errors import JiraOperationError
from ..formatters import format_search_results
from ..models import SearchResult
from ..results import OperationResult

SEARCH_FIELDS = [
    "summary",
    "status",
    "assignee",
    "priority",
    "issuetype",
    "created",
    "updated",
]


def search_issues(
    jql: str,
    *,
    max_results: int = 20,
    fields: list[str] | None = None,
    api: JiraAPI,
) -> OperationResult:
    """Search Jira issues using JQL."""
    limit = min(max_results, 50)
    request_fields = fields or SEARCH_FIELDS

    try:
        data = api.search.enhanced_search(
            jql=jql,
            max_results=limit,
            fields=request_fields,
        )
    except Exception as exc:
        raise JiraOperationError(f"Failed to search issues: {exc}") from exc

    result = SearchResult.model_validate(data)
    return OperationResult.with_data(format_search_results(result, jql=jql), data)


__all__ = ["SEARCH_FIELDS", "search_issues"]
