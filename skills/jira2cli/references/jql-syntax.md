# JQL Syntax

Use this when you need to compose or debug JQL before searching for issues.

## Workflow

1. Print the shared syntax reference:
   - `uvx jira2cli jql-syntax`
2. Compose or correct the query.
3. Validate the query with a narrow search:
   - `uvx jira2cli search '<JQL>' --fields key,summary --max-results <N> --json`
4. For a known issue list, use `key IN (PROJ-1, PROJ-2, PROJ-3) ORDER BY key` with `search`. If Jira rejects a large query, split the keys into smaller `key IN (...)` batches and paginate each batch.
5. If the results are broader than expected, tighten the JQL and rerun the search before taking any later action.
