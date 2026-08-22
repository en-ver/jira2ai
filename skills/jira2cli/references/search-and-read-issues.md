# Search and Read Issues

Use this to inspect Jira issues before deciding on edits, comments, links, worklog analysis, or attachment downloads.

## Workflow

1. If the query is new or failing, start with:
   - `uvx jira2cli jql-syntax`
2. Search for candidate issues. `--max-results` is a per-page limit (default 20; maximum 50):
   - `uvx jira2cli search '<JQL>' --field key --field summary --field status --max-results <N> --json`
3. Continue a search only while the structured output has a non-empty `nextPageToken`. Forward that opaque value unchanged with `--next-page-token`, retaining the exact JQL, fields, and page size; do not use `total` to decide. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page. This Bash loop keeps values safely quoted:

   ```bash
   jql='project = PROJ ORDER BY created DESC'
   page_size=20
   fields=(--field key --field summary --field status)
   token=''

   while :; do
     command=(uvx jira2cli search "$jql" --max-results "$page_size" "${fields[@]}" --json)
     [[ -n "$token" ]] && command+=(--next-page-token "$token")
     page="$("${command[@]}")" || exit $?
     printf '%s\n' "$page"
     token="$(jq -r '.nextPageToken // empty' <<<"$page")"
     [[ -n "$token" ]] || break
   done
   ```

4. Read a specific issue in detail:
   - `uvx jira2cli read <KEY> --json`
5. If you need extra fields beyond the standard read set, repeat `--extra-field` as needed:
   - `uvx jira2cli read <KEY> --extra-field <FIELD_ID> --extra-field <FIELD_ID> --json`
6. Read the existing comments before replying or editing based on discussion context:
   - `uvx jira2cli comments <KEY> --json`
7. Use pagination or reverse ordering when the thread is long or you need the newest entries first:
   - `uvx jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
8. If you need the untouched API payload for a search, issue read, or comments read, rerun the same command with `--raw` instead of `--json`.
9. If the search is still too broad, refine the JQL and rerun instead of acting on partial context.

Summarize the current issue state before any later mutation.
