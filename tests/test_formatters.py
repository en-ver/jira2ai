from __future__ import annotations

from textwrap import dedent

from jira2mcp.formatters import format_search_results
from jira2mcp.models import SearchResult


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
