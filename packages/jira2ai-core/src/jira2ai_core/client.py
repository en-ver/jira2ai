"""Client helpers for Jira AI integrations."""

from jira2py import JiraAPI


def get_api() -> JiraAPI:
    """Create a JiraAPI instance.

    Credentials are resolved by jira2py from environment variables:
    JIRA_URL, JIRA_USER, and JIRA_API_TOKEN.

    Returns:
        Configured JiraAPI instance.

    Raises:
        ValueError: If any required credential is missing.
    """
    return JiraAPI()
