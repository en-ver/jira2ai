"""Issue-link operations."""

from __future__ import annotations

from jira2py import JiraAPI

from ..errors import JiraOperationError
from ..results import OperationResult


def list_link_types(*, api: JiraAPI) -> OperationResult:
    """List available Jira issue link types."""
    try:
        data = api.issue_links.get_link_types()
    except Exception as exc:
        raise JiraOperationError(f"Failed to fetch link types: {exc}") from exc

    link_types = data.get("issueLinkTypes", [])
    lines: list[str] = []
    for link_type in link_types:
        lines.append(
            f'- **{link_type["name"]}**: outward="{link_type.get("outward", "")}", '
            f'inward="{link_type.get("inward", "")}"'
        )

    text = "\n".join(lines) if lines else "No link types configured."
    return OperationResult.with_data(text, data)


def create_issue_link(
    link_type: str,
    outward_issue_key: str,
    inward_issue_key: str,
    *,
    api: JiraAPI,
) -> OperationResult:
    """Create a link between two Jira issues."""
    try:
        api.issue_links.create_link(
            link_type_name=link_type,
            inward_issue_key=inward_issue_key,
            outward_issue_key=outward_issue_key,
        )
    except Exception as exc:
        raise JiraOperationError(f"Failed to create link: {exc}") from exc

    data = {
        "status": "created",
        "link_type": link_type,
        "outward_issue": outward_issue_key,
        "inward_issue": inward_issue_key,
    }
    return OperationResult.with_data(
        f"Created link: {outward_issue_key} {link_type.lower()} {inward_issue_key}",
        data,
    )


def delete_issue_link(link_id: str, *, api: JiraAPI) -> OperationResult:
    """Delete a Jira issue link."""
    try:
        api.issue_links.delete_link(link_id=link_id)
    except Exception as exc:
        raise JiraOperationError(f"Failed to delete link {link_id}: {exc}") from exc

    return OperationResult.with_data(
        f"Deleted issue link {link_id}",
        {"status": "deleted", "link_id": link_id},
    )


__all__ = ["create_issue_link", "delete_issue_link", "list_link_types"]
