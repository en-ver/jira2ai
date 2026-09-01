# Transitions and Saved Filters

Use this when you need workflow transition metadata, need to apply a transition, or want to discover/run saved Jira filters.

## Workflow transitions

A Jira transition action is not a status update. Its action ID is distinct from its destination status ID, and a looped action can intentionally leave the issue in the same status. Do not guess an action/name or assume a workflow state exists in the project.

1. Read the current issue and fields expected to change:
   ```bash
   uvx jira2cli read <KEY> --fields summary,status,<CHANGED_FIELD> --json
   ```
2. Discover fresh expanded structured metadata. Include unavailable transitions only when diagnosing why an action is absent or blocked; they are never valid mutation choices. Focus an already-current action ID when its metadata is large:
   ```bash
   uvx jira2cli transitions <KEY> --json
   uvx jira2cli transitions <KEY> --include-unavailable --json
   uvx jira2cli transitions <KEY> --transition-id <ACTION_ID> --json
   ```
3. Choose a freshly discovered available **transition action ID**. Inspect availability, screen/conditional/global/looped indicators, required fields, schema, operations, allowed values, defaults, autocomplete, and configuration. The destination status ID does not replace the action ID.
4. After confirmation, submit one native Jira request. `--fields-json` and `--update-json` each require a JSON object and are delegated unchanged. They do not convert Markdown to ADF, add comment/worklog convenience flags, validate the screen locally, provide checked/prepare/apply/pathfinding behavior, automatically verify, or promise ACID/idempotent execution:
   ```bash
   uvx jira2cli transition <KEY> <ACTION_ID> \
     --fields-json '{"resolution":{"name":"Done"}}' --json

   # Only if the current transition metadata permits a native comment add.
   uvx jira2cli transition <KEY> <ACTION_ID> \
     --update-json '{"comment":[{"add":{"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Approved for release."}]}]}}}]}' \
     --json

   # Native worklog add is also conditional on the current operations metadata.
   uvx jira2cli transition <KEY> <ACTION_ID> \
     --update-json '{"worklog":[{"add":{"timeSpent":"30m","comment":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Release verification"}]}]}}}]}' \
     --json
   ```

   The `fields` object contains native field values. The `update` object contains native operation arrays; native `update.comment` bodies must already be Jira-native ADF, and the worklog bodies above are likewise ADF. Do not use the exact same field key in both objects: `jira2py` rejects that overlap before POST. Inline JSON can enter shell history. Jira fields, comments, and worklogs are persistent data, not secret storage; never place credentials or secrets in them.
5. Jira commonly responds `204 No Content`, so acceptance returns no issue object and is not proof of the resulting status. Reread the issue status and changed fields. Inspect `comments`, `worklogs`, or `changelogs` when the request could affect them.

For `400`, return to fresh metadata and correct the screen/required/schema/allowed value/operation shape, or determine whether the configured account lacks permission to transition the issue. For `409`, a timeout, or `5xx`, delivery or state may be unknown: reread the issue, current metadata, and relevant comments/worklogs or changelog before deciding on one new request. Do **not** blindly retry a transition or native update operation; either can be non-idempotent.

## Saved filters

1. List visible filters:
   - `uvx jira2cli filters --json`
2. Narrow by name when needed:
   - `uvx jira2cli filters --query <text> --json`
3. Capture the exact saved filter ID before running it.
4. Run the filter through the normal search flow. Unlike singular `read`, `filter-run` is a multi-issue projected read: one invocation returns one page and requests `--fields` for every issue in that page. `--max-results` is a per-page limit (default 20; maximum 50):
   - `uvx jira2cli filter-run <FILTER_ID> --fields key,summary --max-results <N> --json`
5. `--fields` is optional and may appear at most once as comma-delimited selectors, for example `--fields key,summary`. If omitted, fields default to `summary, status, assignee, priority, issuetype, created, updated`. Requested fields may still be absent or null. Projection is whole-field: `assignee` may include Jira-permitted nested identity, email, and avatar data; envelope metadata may remain. Plain output remains the helper's fixed compact view; use structured `--json` or `--raw` and local reduction with `jq` for arbitrary requested fields.
6. Continue only while structured `--json` or `--raw` output has a non-empty opaque `nextPageToken`; forward it unchanged with `--next-page-token`. Do not use `total` to decide. Keep the exact filter ID, fields, and page size stable, and do not edit the saved filter while continuing. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page. This loop captures each complete page and emits only issue keys:

   ```bash
   filter_id=10400
   page_size=20
   fields=(--fields key)
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
