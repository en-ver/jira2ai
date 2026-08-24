# Search and Read Issues

Use this to inspect Jira issues before deciding on edits, comments, links, worklog analysis, or attachment downloads.

## Workflow

1. If the query is new or failing, start with:
   - `uvx jira2cli jql-syntax`
2. Search for candidate issues. Unlike singular `read`, `search` is a multi-issue projected read: one invocation returns one page and requests `--fields` for every issue in that page. `--max-results` is a per-page limit (default 20; maximum 50):
   - `uvx jira2cli search '<JQL>' --fields key,summary,status --max-results <N> --json`

   `--fields` is optional and may appear at most once as comma-delimited selectors, for example `--fields key,summary`. If omitted, fields default to `summary, status, assignee, priority, issuetype, created, updated`. Requested fields may still be absent or null. Projection is whole-field: `assignee` may include Jira-permitted nested identity, email, and avatar data. Jira envelope metadata may remain, including issue-envelope members such as `id`, `key`, and `self`, plus search metadata such as `isLast`, `nextPageToken`, and optional `warnings`, `names`, or `schema`. Plain output remains the helper's fixed compact view; use structured `--json` or `--raw` and local reduction with `jq` for arbitrary requested fields.

   For known issue keys, use one JQL batch such as `key IN (PROJ-1, PROJ-2, PROJ-3) ORDER BY key`. If Jira accepts a 325-key query and its result set remains stable, 50 results per page require at most seven search pages—not 325 singular `read` calls. If Jira rejects a large query, split the keys into smaller `key IN (...)` batches and paginate each batch.
3. Continue a search only while structured `--json` or `--raw` output has a non-empty `nextPageToken`. Forward that opaque value unchanged with `--next-page-token`, retaining the exact JQL, fields, and page size; do not use `total` to decide. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page. This Bash loop keeps values safely quoted, captures each complete page, and emits only issue keys:

   ```bash
   jql='project = PROJ ORDER BY created DESC'
   page_size=20
   fields=(--fields key)
   token=''
   rows_received=0

   while :; do
     command=(uvx jira2cli search "$jql" --max-results "$page_size" "${fields[@]}" --json)
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

4. Read a specific issue with the exact fields needed:
   - `uvx jira2cli read <KEY> --fields summary,status,description --json`
5. Add every needed field key, ID, or endpoint-supported selector to the one required CSV:
   - `uvx jira2cli read <KEY> --fields summary,<FIELD_ID>,<FIELD_ID> --json`

   CSV segments are trimmed and must be non-empty. `--json` preserves raw Jira values, including ADF; wildcard or negative selectors can still return broad responses.
6. An embedded `comment` or `worklog` field in a search projection may be partial. For a complete per-issue collection, use its dedicated paginated command rather than the embedded field:
   - `uvx jira2cli comments <KEY> --json`
   - `uvx jira2cli worklogs <KEY> --json`
7. Use pagination or reverse ordering when the comment thread is long or you need the newest entries first:
   - `uvx jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
8. If you need API-oriented output for a search or comments read, rerun the same command with `--raw` instead of `--json`. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes. `read` has no `--raw`; use `read --json` for its unchanged Jira response.
9. If the search is still too broad, refine the JQL and rerun instead of acting on partial context.

Summarize the current issue state before any later mutation.
