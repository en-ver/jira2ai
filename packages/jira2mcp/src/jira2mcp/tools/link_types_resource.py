"""MCP resource exposing available Jira issue link types."""

from fastmcp.dependencies import Depends
from jira2ai_core.client import get_api
from jira2ai_core.operations.links import list_link_types as _list_link_types
from jira2py import JiraAPI

from .server import tools


@tools.resource("data://link-types")
def list_link_types(api: JiraAPI = Depends(get_api)) -> str:
    """Available issue link types in this Jira instance.

    Each link type has a name, an inward description, and an outward description.
    For example, link type "Blocks" has inward="is blocked by" and outward="blocks".

    Use the link type name with the jira_add_link tool to create links between issues.
    """
    return _list_link_types(api=api).text
