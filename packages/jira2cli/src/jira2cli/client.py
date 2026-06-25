"""Client helpers for jira2cli."""

from jira2py import JiraAPI


def get_api() -> JiraAPI:
    """Create a JiraAPI instance from environment-based credentials."""
    return JiraAPI()


__all__ = ["get_api"]
