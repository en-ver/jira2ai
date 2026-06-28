"""Jira tools sub-server — all tools registered here and mounted by the main server."""

# Import all tool modules to trigger registration
from . import (  # noqa: F401
    add_link,
    attachment,
    auth,
    comment,
    comments,
    create,
    delete_link,
    edit,
    fields,
    filters,
    issue_links,
    jql_syntax_prompt,
    link_types_resource,
    metadata,
    projects,
    read,
    search,
    transitions,
    users,
    worklogs,
)
from .server import tools

__all__ = ["tools"]
