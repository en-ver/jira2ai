# JQL Syntax

Use this when you need to compose or debug JQL before searching for issues.

## Workflow

1. Print the shared syntax reference:
   - `uv run jira2cli jql-syntax`
2. Compose or correct the query.
3. Validate the query with a narrow search:
   - `uv run jira2cli search '<JQL>' --field key --field summary --max-results <N> --json`
4. If the results are broader than expected, tighten the JQL and rerun the search before taking any later action.
