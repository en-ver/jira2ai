"""Project metadata operations."""

from __future__ import annotations

from jira2py import JiraAPI

from ..errors import JiraOperationError
from ..models import ProjectSearchResult
from ..results import OperationResult


def list_projects(
    query: str | None = None,
    *,
    api: JiraAPI,
) -> OperationResult:
    """List Jira projects accessible to the current user."""
    try:
        data = api.projects.search_projects(
            query=query,
            max_results=100,
            extra_params={"orderBy": "name"},
        )
    except Exception as exc:
        raise JiraOperationError(f"Failed to fetch projects: {exc}") from exc

    result = ProjectSearchResult.model_validate(data)

    if not result.values:
        if query:
            text = f'No projects found matching "{query}"'
        else:
            text = "No projects found"
        return OperationResult.with_data(text, data)

    lines: list[str] = []
    header = f'Projects matching "{query}"' if query else "Projects"
    lines.append(f"{header}:\n")

    for project in result.values:
        lines.append(f"  {project.key} — {project.name}")

    if not result.isLast:
        if result.total is not None:
            more = result.total - len(result.values)
            lines.append(f"\n  ... and {more} more (refine your search)")
        else:
            lines.append("\n  ... more results available (refine your search)")

    return OperationResult.with_data("\n".join(lines), data)


__all__ = ["list_projects"]
