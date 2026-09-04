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

`fields`, `fields-list`, `project`, `projects`, `statuses`, `priorities`, `users`, `link-types`, `jql-syntax`, `filters`, `filter-run`

### Issues, comments, and links

`create`, `edit`, `comment`, `comment-update`, `comment-delete`, `issue-links`, `add-link`, `delete-link`

### Attachments and worklogs

`attachment`, `attachment-list`, `attachment-read`, `attachment-download`, `attachment-upload`, `attachment-delete`, `worklogs`, `worklog-add`, `worklog-update`, `worklog-delete`, `worklog-report`

Most structured commands accept `--json` for helper output. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes. `read` does not support `--raw`; use its `--json` option for the unchanged Jira response. Do not combine `--raw` and `--json` on commands that support both. `filter-run` resolves a saved filter's JQL and returns the same search-shaped result as `search`.

`read` requires exactly one `--fields FIELD[,FIELD...]` option. Its CSV segments are trimmed, must be non-empty, and are forwarded in order as Jira field keys, IDs, or endpoint-supported selectors. `--json` bypasses text formatting and preserves the returned Jira object, including ADF. Selectors such as `*all`, `*navigable`, or negative selectors can still return broad responses; request only what is needed.

## Mentions in high-level writes

High-level Markdown writes recognize the canonical Jira mention `[~accountId:<id>]`: issue descriptions, compatible rich-text string values in `--fields-json` (including `environment` and supported custom textarea fields), comment add/update bodies, and worklog add/update comments. It produces one semantic ADF mention, and Jira may notify the referenced account.

Only the unescaped canonical form is a mention. Escaped, malformed, code, link, and image forms remain text. This write-only behavior does not apply to native `transition --fields-json` or `--update-json` values, which must already use Jira-native shapes and ADF where required.

Formatted issue, comment, and worklog Markdown is presentation-only and may lose mention identity when edited or written back. For identity-safe edits, preserve raw ADF from `read --json` for issue fields and structured `comments --json` or `worklogs --json` output for their bodies; do not write formatted text back when mention identity matters.

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

## Field catalog

`fields-list` returns exactly one Jira `/field/search` page. It defaults to `--start-at 0 --max-results 20` and accepts optional `--project-key`, `--query`, canonical `--field-ids ID[,ID...]`, and `--field-types system[,custom]`. The normal view is concise (field name and canonical ID); `--json` and `--raw` return the complete Jira page envelope, including `values`, `startAt`, `maxResults`, `total`, `isLast`, and any other Jira properties.

To continue, retain every filter and use the returned `startAt + len(values)` as the next `--start-at`; stop when Jira reports `isLast`. Jira can cap the requested page size, so use its returned metadata. The endpoint is documented for classic projects. `--project-key` only supplies Jira project context/access filtering: it does **not** identify fields applicable to an issue type, Create screen, or Edit screen. Continue to use `fields` for issue-type, create-screen, and edit-screen metadata.

## Changelog history

`changelogs <KEY>` retrieves the complete issue history: it follows every Jira GET page before returning one helper-owned envelope, `{"issue_key": "<KEY>", "changelogs": [...]}`. Optional `--created-at-or-after` and `--created-before` are client-side ISO-8601 filters applied only after retrieval with the half-open interval `created_at_or_after <= created < created_before`; they do not restrict Jira's GET requests. Optional `--field-ids ID[,ID...]` retains only changelog items whose raw `fieldId` exactly matches a canonical field ID, dropping history events with no retained items.

`changelogs` normally returns every retained event. Supplying `--result-max-results N` enables local event pagination; `--result-start-at` defaults to `0` and requires `--result-max-results` when nonzero. Jira's complete history is still fetched before timestamp and field-ID filters and the result slice. Paged JSON/raw output adds helper-owned `result_page` metadata; it is not Jira server pagination.

Use `changelogs-by-ids <KEY> --changelog-ids ID[,ID...]` only when the exact changelog IDs are already known, normally from `changelogs`. It uses Jira's distinct known-ID POST endpoint. The plural CSV option is required exactly once; segments are trimmed base-10 integers and preserve order and duplicates. It also accepts `--field-ids ID[,ID...]` with the same exact raw-`fieldId` filtering. Jira controls the POST response order; this known-ID operation has no result pagination, so batch fewer IDs when a smaller response is needed.

Both commands render condensed text normally. `--json` and `--raw` render the same normalized helper-owned envelope, not untouched HTTP pages or bytes. Complete history and structured output can be large; terminals or external harnesses can still clip output.

## Workflow transitions

A transition action is a current workflow action, not a status update. Work from a fresh issue read and fresh transition metadata so the ID, availability, and screen rules are current:

1. Read the current issue and the fields that you expect to change:
   ```bash
   uvx jira2cli read PROJ-123 --fields summary,status,resolution --json
   ```
2. Discover expanded structured metadata. Use `--include-unavailable` only to diagnose why an action is unavailable; never submit an unavailable action. Focus a known current action when its metadata is large:
   ```bash
   uvx jira2cli transitions PROJ-123 --json
   # Diagnostic only when investigating a blocked or absent action.
   uvx jira2cli transitions PROJ-123 --include-unavailable --json
   uvx jira2cli transitions PROJ-123 --transition-id 31 --json
   ```
   Inspect availability, screen/conditional/global/looped indicators, required fields, schema, operations, allowed values, defaults, autocomplete, and configuration. `31` is a **transition action ID**; it is not the destination status ID. A looped action can intentionally leave the issue in the same status.
3. Choose a fresh available transition action ID and submit one native Jira request. `--fields-json` is a JSON object of field values; `--update-json` is a JSON object of native operation arrays. The CLI forwards both unchanged: it does not convert Markdown to Atlassian Document Format (ADF), add comment/worklog flags, validate screen values locally, or promise ACID/idempotent behavior.

   ```bash
   uvx jira2cli transition PROJ-123 31 \
     --fields-json '{"resolution":{"name":"Done"}}' --json

   # Only when this transition metadata permits comment operations.
   uvx jira2cli transition PROJ-123 31 \
     --update-json '{"comment":[{"add":{"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Approved for release."}]}]}}}]}' \
     --json

   # Likewise, use a native worklog add shape only when the metadata permits it.
   uvx jira2cli transition PROJ-123 31 \
     --update-json '{"worklog":[{"add":{"timeSpent":"30m","comment":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Release verification"}]}]}}}]}' \
     --json
   ```

   Do not use the exact same field key in both objects: Jira may define different semantics, and `jira2py` rejects exact overlap before the POST. Native `update.comment` bodies must already be Jira-native ADF, and `update` operation objects must already have Jira-native shapes. Inline CLI JSON can enter shell history; persistent Jira fields, comments, and worklogs are not secret storage.
4. Jira commonly replies `204 No Content`: acceptance returns no issue object and does not verify the outcome. Reread the issue status and changed fields. Inspect `comments`, `worklogs`, or `changelogs` when an operation could have affected them.

A `400` usually means the fresh metadata, screen, required fields, schema, allowed values, or operation shape needs correction, or the configured account lacks permission to transition the issue. A `409`, timeout, or `5xx` can leave delivery or final state uncertain. In all of those cases, reread the issue and current transition metadata (and comments/worklogs or changelog when relevant) before deciding on one new request. Do **not** blindly retry: a transition or native comment/worklog operation can be non-idempotent.

## Examples

```bash
# Discover accessible projects and create/edit fields before a write.
uvx jira2cli projects --json
uvx jira2cli fields --project-key PROJ --issue-type Task --json
uvx jira2cli fields-list --project-key PROJ --field-types system --max-results 20 --json

# Read and search.
uvx jira2cli read PROJ-123 --fields summary,labels --json
uvx jira2cli search 'project = PROJ ORDER BY created DESC' --fields key,summary --json

# Inspect current expanded workflow choices, then apply a fresh action ID.
uvx jira2cli transitions PROJ-123 --json
uvx jira2cli transition PROJ-123 31 --json

# Reuse a saved filter.
uvx jira2cli filters --query mine --json
uvx jira2cli filter-run 10400 --fields key,summary --json

# Inspect changelog history, attachments, and worklogs.
uvx jira2cli changelogs PROJ-123 --field-ids summary --result-max-results 20 --json
uvx jira2cli changelogs-by-ids PROJ-123 --changelog-ids 10001,10002 --field-ids summary --json
uvx jira2cli attachment-list PROJ-123 --json
uvx jira2cli worklogs PROJ-123 --json
uvx jira2cli worklog-report --start-date 2026-06-12 --end-date 2026-06-13 --jql 'issue = PROJ-123' --json
```

Worklog-report dates are UTC and the end date is inclusive. It selects issues only with `--jql`; `--max-issues` defaults to 100 and limits the scanned issues. Results depend on the configured account's issue and worklog visibility.

## Local checkout contributors

From the repository root after workspace setup, contributors can run the checked-out CLI with:

```bash
uv run --locked --package jira2cli jira2cli --help
```

## Safety and capabilities

Dedicated description parameters and comment-command bodies accept Markdown and convert it to ADF. Plain `read` output renders selected rich-text Jira fields as Markdown, while `read --json` preserves the raw Jira data. Use `fields` before create or edit; `users` before choosing a user; `transitions` before changing status; and `link-types` before creating links. For a transition, follow the fresh metadata, native JSON, reread, and no-blind-retry workflow above. Read the current issue before an update or destructive action, use exact IDs, and confirm the intended fields, transition, comment, attachment, link, or worklog before mutating Jira. Jira permissions control what the configured account can read or write.

The optional [Pi skill](https://github.com/en-ver/jira2ai/tree/main/skills/jira2cli) is a source-checkout template for agent workflows. Load it explicitly as `<path-to-jira2ai>/skills/jira2cli`; UVX runs the CLI but does not install or auto-discover the skill.

## License

MIT
