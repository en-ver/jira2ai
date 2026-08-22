# Transitions and Saved Filters

Use this when you need workflow transition metadata, need to apply a transition, or want to discover/run saved Jira filters.

## Workflow transitions

1. Read the issue first:
   - `uvx jira2cli read <KEY> --json`
2. List the available transitions:
   - `uvx jira2cli transitions <KEY> --json`
3. Confirm the exact transition ID or exact transition name.
4. After confirmation only, run:
   - `uvx jira2cli transition <KEY> <TRANSITION_ID_OR_NAME> --json`

Do not guess transition names or assume a workflow state exists in the target project.

## Saved filters

1. List visible filters:
   - `uvx jira2cli filters --json`
2. Narrow by name when needed:
   - `uvx jira2cli filters --query <text> --json`
3. Capture the exact saved filter ID before running it.
4. Run the filter through the normal search flow. `--max-results` is a per-page limit (default 20; maximum 50):
   - `uvx jira2cli filter-run <FILTER_ID> --field key --field summary --max-results <N> --json`
5. Add repeated `--field` options when you need more search fields.
6. Continue only while structured `--json` output has a non-empty `nextPageToken`; forward it unchanged with `--next-page-token`. Do not use `total` to decide. Keep the exact filter ID, fields, and page size stable, and do not edit the saved filter while continuing. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page:

   ```bash
   filter_id=10400
   page_size=20
   fields=(--field key --field summary)
   token=''

   while :; do
     command=(uvx jira2cli filter-run "$filter_id" --max-results "$page_size" "${fields[@]}" --json)
     [[ -n "$token" ]] && command+=(--next-page-token "$token")
     page="$("${command[@]}")" || exit $?
     printf '%s\n' "$page"
     token="$(jq -r '.nextPageToken // empty' <<<"$page")"
     [[ -n "$token" ]] || break
   done
   ```

`filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.
