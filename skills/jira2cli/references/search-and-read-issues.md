# Search and Read Issues

Use this to inspect Jira issues before deciding on edits, comments, links, worklog analysis, or attachment downloads.

## Workflow

1. If the query is new or failing, start with:
   - `uv run jira2cli jql-syntax`
2. Search for candidate issues:
   - `uv run jira2cli search '<JQL>' --field key --field summary --field status --max-results <N> --json`
3. Read a specific issue in detail:
   - `uv run jira2cli read <KEY> --json`
4. If you need extra fields beyond the standard read set, repeat `--extra-field` as needed:
   - `uv run jira2cli read <KEY> --extra-field <FIELD_ID> --extra-field <FIELD_ID> --json`
5. Read the existing comments before replying or editing based on discussion context:
   - `uv run jira2cli comments <KEY> --json`
6. Use pagination or reverse ordering when the thread is long or you need the newest entries first:
   - `uv run jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
7. If you need the untouched API payload for a search, issue read, or comments read, rerun the same command with `--raw` instead of `--json`.
8. If the search is still too broad, refine the JQL and rerun instead of acting on partial context.

Summarize the current issue state before any later mutation.
