from __future__ import annotations

from textwrap import dedent
from typing import cast

from jira2mcp.formatters import format_issue_full, format_search_results
from jira2mcp.models import JiraIssue, SearchResult


def test_format_issue_full_renders_current_markdown_output(
    sample_issue_data: dict[str, object],
) -> None:
    issue = JiraIssue.model_validate(sample_issue_data)

    formatted = format_issue_full(
        issue,
        url="https://example.atlassian.net/browse/PROJ-123",
        requested_fields=["summary", "customfield_10001", "customfield_10002"],
        field_names=cast(dict[str, str], sample_issue_data["names"]),
    )

    assert (
        formatted
        == dedent(
            """\
        Key: PROJ-123
        Summary: Fix thing
        Status: In Progress
        Type: Bug
        Priority: High
        Assignee: Alice
        Reporter: Bob
        Created: 2026-01-02
        Updated: 2026-01-03
        Labels: backend, urgent
        Components: API
        Fix Versions: 1.2.3
        URL: https://example.atlassian.net/browse/PROJ-123
        Comments: 2

        --- [ATTACHMENTS (1)] ---
        - debug.log (id: 7, text/plain, 1.5 KB)

        --- [SUBTASKS (1)] ---
        - PROJ-124: subtask summary [To Do]

        --- [ISSUE LINKS (1)] ---
        - blocks PROJ-200: linked issue [Done] (link id: 55)

        --- [DESCRIPTION] ---
        Hello **world**

        --- [ADDITIONAL FIELDS] ---
        --- [ACCEPTANCE CRITERIA (CUSTOMFIELD_10001)] ---
        Extra field

        ```json
        {
          "customfield_10002": {
            "foo": "bar"
          }
        }
        ```
        """
        ).strip()
    )


def test_format_search_results_includes_paging_hint() -> None:
    result = SearchResult.model_validate(
        {
            "issues": [
                {
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "One",
                        "status": {"name": "Open"},
                        "assignee": {"displayName": "Alice"},
                    },
                },
                {
                    "key": "PROJ-2",
                    "fields": {
                        "summary": "Two",
                        "status": {"name": "Done"},
                        "assignee": None,
                    },
                },
            ],
            "nextPageToken": "tok",
        }
    )

    assert (
        format_search_results(result, jql="project = PROJ")
        == dedent(
            """\
        Found 2 issue(s)

        PROJ-1 — One [Open] (Alice)
        PROJ-2 — Two [Done] (Unassigned)

        (more results available — refine JQL or increase max_results)
        """
        ).strip()
    )
