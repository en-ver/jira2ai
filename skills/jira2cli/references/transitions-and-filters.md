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
5. `--field` is singular and repeatable: `--field key --field summary`; `--fields` does not exist, and values are not comma-split. If omitted, fields default to `summary, status, assignee, priority, issuetype, created, updated`. Projection is whole-field: `assignee` may include Jira-permitted nested identity, email, and avatar data; envelope metadata may remain. Plain output remains the helper's fixed compact view; use structured output and local reduction with `jq` for arbitrary requested fields.
6. Continue only while structured `--json` output has a non-empty `nextPageToken`; forward it unchanged with `--next-page-token`. Do not use `total` to decide. Keep the exact filter ID, fields, and page size stable, and do not edit the saved filter while continuing. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page. This loop captures each complete page and emits only issue keys:

   ```bash
   filter_id=10400
   page_size=20
   fields=(--field key)
   token=''
   rows_received=0

   while :; do
     command=(uvx jira2cli filter-run "$filter_id" --max-results "$page_size" "${fields[@]}" --json)
     [[ -n "$token" ]] && command+=(--next-page-token "$token")

     page="$("${command[@]}")" || exit $?

     page_rows="$(jq '.issues | length' <<<"$page")" || exit $?
     rows_received=$((rows_received + page_rows))

     jq -r '.issues[].key' <<<"$page" || exit $?
     jq -c '.warnings[]? | {jira_warning: .}' <<<"$page" >&2 || exit $?

     token="$(jq -r '.nextPageToken // empty' <<<"$page")" || exit $?
     [[ -n "$token" ]] || break
   done

   printf '{"rows_received":%d}\n' "$rows_received" >&2
   ```

   `page_rows` is the number of issue rows received on that page, and `rows_received` is the sum of rows observed across fetched pages. It is not an authoritative Jira-wide `total` or necessarily a unique-issue count: search results can change while paging, so duplicates or omissions remain possible. `.warnings` contains optional Jira/API warnings; they do not report clipping imposed by an agent harness, terminal, or other external consumer. Absence of Jira warnings does not prove that an external display retained all output. This technique protects callers when clipping occurs after shell capture. If a harness terminates or limits subprocess output before command substitution completes, reduction must happen inside that boundary; this option deliberately adds no built-in compact mode.

`filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.
