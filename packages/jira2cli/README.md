# jira2cli

A flat CLI for **Jira Cloud**. Requires Python >=3.13.

`jira2cli` is published on PyPI. Install [uv](https://docs.astral.sh/uv/) and run it with `uvx jira2cli`; for repository checkout and contributor setup, see the [contributing guide](https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md).

It does not support Jira Server or Data Center, and does not provide dedicated issue assignment, issue delete/archive, sprint/board/epic, or admin-configuration operations.

## Authentication and usage

Authenticate with either an explicit credentials file or environment variables:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"

uvx jira2cli auth-status
uvx jira2cli read PROJ-123 --fields summary,status --json
```

An explicit credentials file takes precedence over the environment:

```bash
uvx jira2cli --credentials-file ~/.config/jira-cloud.json me --json
```

```json
{
  "url": "https://yourcompany.atlassian.net",
  "username": "you@company.com",
  "api_token": "your-api-token"
}
```

There is no default credentials-file path and no `JIRA_CREDENTIALS_FILE` environment variable. Create a token in your [Atlassian account](https://id.atlassian.com/manage-profile/security/api-tokens); do not commit, print, or share it.

## Commands

Run `uvx jira2cli --help` for the current command and option help.

### Identity

`auth-status`, `me`

### Reads, changelog history, search, and transitions

`read`, `comments`, `changelogs`, `changelogs-by-ids`, `search`, `transitions`, `transition`

### Metadata and saved filters

`fields`, `project`, `projects`, `statuses`, `priorities`, `users`, `link-types`, `jql-syntax`, `filters`, `filter-run`

### Issues, comments, and links

`create`, `edit`, `comment`, `comment-update`, `comment-delete`, `issue-links`, `add-link`, `delete-link`

### Attachments and worklogs

`attachment`, `attachment-list`, `attachment-read`, `attachment-download`, `attachment-upload`, `attachment-delete`, `worklogs`, `worklog-add`, `worklog-update`, `worklog-delete`, `worklog-report`

Most structured commands accept `--json` for helper output. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes. `read` does not support `--raw`; use its `--json` option for the unchanged Jira response. Do not combine `--raw` and `--json` on commands that support both. `filter-run` resolves a saved filter's JQL and returns the same search-shaped result as `search`.

`read` requires exactly one `--fields FIELD[,FIELD...]` option. Its CSV segments are trimmed, must be non-empty, and are forwarded in order as Jira field keys, IDs, or endpoint-supported selectors. `--json` bypasses text formatting and preserves the returned Jira object, including ADF. Selectors such as `*all`, `*navigable`, or negative selectors can still return broad responses; request only what is needed.

## Multi-issue projected search and pagination

Unlike singular `read`, `search` and `filter-run` are multi-issue projected reads. Each invocation returns one page and requests the selected `--fields` for every issue in that page. A requested field can still be absent or null. Use structured `--json` or `--raw` to inspect arbitrary projected fields: plain output is a fixed compact view.

Each `search` or `filter-run` invocation returns exactly one page. `--max-results` defaults to 20 and has a 50-item ceiling; it is a **per-page** limit. Structured output preserves the opaque `nextPageToken`. When it is non-empty, pass it unchanged as `--next-page-token` on the next invocation; stop when it is absent or empty. Do not use `total` to decide whether to continue. Keep the JQL (or saved filter), requested `--fields` value, and `--max-results` unchanged for every page. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page.

`--fields` is optional and may appear at most once as comma-delimited selectors, for example `--fields key,summary`; values are trimmed and empty CSV segments are rejected. If omitted, fields default to `summary, status, assignee, priority, issuetype, created, updated`. Projection is whole-field: `assignee` may include Jira-permitted nested identity, email, and avatar data. Jira envelope metadata may remain, including issue-envelope members such as `id`, `key`, and `self`, plus search metadata such as `isLast`, `nextPageToken`, and optional `warnings`, `names`, or `schema`.

For a known issue list, search it as a batch with JQL. If Jira rejects a large query, split the keys into smaller `key IN (...)` batches and paginate each batch:

```bash
uvx jira2cli search 'key IN (PROJ-1, PROJ-2, PROJ-3) ORDER BY key' \
  --fields key,summary,status,customfield_12345 --max-results 50 --json
```

An embedded `comment` or `worklog` field in a search projection may be partial. For complete per-issue collections, use the dedicated paginated `comments <KEY>` or `worklogs <KEY>` command instead.

This Bash example uses arrays so the JQL and opaque token remain safely quoted, captures each complete page, and emits only issue keys:

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

For saved filters, use the same loop with `filter-run <FILTER_ID>` in place of `search <JQL>`, retaining the exact filter ID, fields, and page size. The same counts and warning limitations apply. Do not edit the saved filter until the continuation is complete.

## Changelog history

`changelogs <KEY>` retrieves the complete issue history: it follows every Jira GET page before returning one helper-owned envelope, `{"issue_key": "<KEY>", "changelogs": [...]}`. Optional `--created-at-or-after` and `--created-before` are client-side ISO-8601 filters applied only after retrieval with the half-open interval `created_at_or_after <= created < created_before`; they do not restrict Jira's GET requests.

Use `changelogs-by-ids <KEY> --changelog-ids ID[,ID...]` only when the exact changelog IDs are already known, normally from `changelogs`. It uses Jira's distinct known-ID POST endpoint. The plural CSV option is required exactly once; segments are trimmed base-10 integers and preserve order and duplicates. Jira controls the POST response order.

Both commands render condensed text normally. `--json` and `--raw` render the same normalized helper-owned envelope, not untouched HTTP pages or bytes. Complete history and structured output can be large; neither command applies a result-size cap, and terminals or external harnesses can still clip output.

## Examples

```bash
# Discover accessible projects and create/edit fields before a write.
uvx jira2cli projects --json
uvx jira2cli fields --project-key PROJ --issue-type Task --json

# Read and search.
uvx jira2cli read PROJ-123 --fields summary,labels --json
uvx jira2cli search 'project = PROJ ORDER BY created DESC' --fields key,summary --json

# Inspect workflow choices before applying one.
uvx jira2cli transitions PROJ-123 --json
uvx jira2cli transition PROJ-123 "Start Progress" --json

# Reuse a saved filter.
uvx jira2cli filters --query mine --json
uvx jira2cli filter-run 10400 --fields key,summary --json

# Inspect changelog history, attachments, and worklogs.
uvx jira2cli changelogs PROJ-123 --created-at-or-after 2026-08-01T00:00:00Z --json
uvx jira2cli changelogs-by-ids PROJ-123 --changelog-ids 10001,10002 --json
uvx jira2cli attachment-list PROJ-123 --json
uvx jira2cli worklogs PROJ-123 --json
uvx jira2cli worklog-report --start-date 2026-06-12 --end-date 2026-06-13 --jql 'issue = PROJ-123' --json
```

Worklog-report dates are UTC and the end date is inclusive. It selects issues only with `--jql`; `--max-issues` defaults to 100 and limits the scanned issues. Results depend on the configured account's issue and worklog visibility.

## Local checkout contributors

From the repository root after workspace setup, contributors can run the checked-out CLI with:

```bash
uv run --locked jira2cli --help
```

## Safety and capabilities

Descriptions and comments accept Markdown. Plain `read` output renders selected rich-text Jira fields as Markdown, while `read --json` preserves the raw Jira data. Use `fields` before create or edit; `users` before choosing a user; `transitions` before changing status; and `link-types` before creating links. Read the current issue before an update or destructive action, use exact IDs, and confirm the intended fields, transition, comment, attachment, link, or worklog before mutating Jira. Jira permissions control what the configured account can read or write.

The optional [Pi skill](https://github.com/en-ver/jira2ai/tree/main/skills/jira2cli) is a source-checkout template for agent workflows. Load it explicitly as `<path-to-jira2ai>/skills/jira2cli`; UVX runs the CLI but does not install or auto-discover the skill.

## License

MIT
