"""Jira tools sub-server — all tools registered here and mounted by the main server."""

# Import all tool modules to trigger registration
from . import (  # noqa: F401
    add_link,
    attachment,
    comment,
    comments,
    create,
    delete_link,
    edit,
    fields,
    jql_syntax_prompt,
    link_types_resource,
    projects,
    read,
    search,
    users,
    worklogs,
)
from .server import tools

__all__ = ["tools"]
