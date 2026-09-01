---
name: jira2cli
description: Jira Cloud workflows through the published `jira2cli` CLI. Use when verifying `jira2cli`, discovering Jira metadata, reading issues, comments, changelog histories, or worklogs, working with saved filters and transitions, downloading/uploading attachments, or safely mutating Jira issues.
---

# jira2cli

Use the published `jira2cli` CLI for Jira Cloud workflows with `uvx jira2cli`. It requires Python >=3.13.

`jira2cli` is **Jira Cloud only**. Do not treat it as Jira Server/Data Center support.

It also does **not** provide dedicated issue assign commands, issue delete/archive flows, sprint/board/epic operations, or admin-heavy Jira configuration tooling.

## References

- [references/install-auth.md](references/install-auth.md) — Load when you need the consumer command prefix, CLI verification, Jira auth setup, or local maintainer verification.
- [references/project-discovery.md](references/project-discovery.md) — Load when you need to resolve the right Jira project key or discover issue types with `fields --project-key`.
- [references/field-catalog.md](references/field-catalog.md) — Load when you need one searchable page of canonical Jira field IDs, names, types, or project-context metadata.
- [references/field-metadata.md](references/field-metadata.md) — Load before create/edit work when you need required fields, editable fields, or allowed values.
- [references/user-identity-lookup.md](references/user-identity-lookup.md) — Load when a Jira user field needs an `accountId` or exact display name.
- [references/jql-syntax.md](references/jql-syntax.md) — Load when composing or debugging JQL.
- [references/search-and-read-issues.md](references/search-and-read-issues.md) — Load when you need to search issues, choose explicit issue fields, read details, or page through comments.
- [references/changelog-history.md](references/changelog-history.md) — Load when you need complete issue change history, local timestamp filtering, or retrieval by known changelog IDs.
- [references/transitions-and-filters.md](references/transitions-and-filters.md) — Load when you need workflow transitions, saved filter discovery, or `filter-run` guidance.
- [references/worklog-report.md](references/worklog-report.md) — Load when you need JQL-based worklog reporting details.
- [references/worklog-management.md](references/worklog-management.md) — Load when you need issue-specific worklog list/add/update/delete workflows.
- [references/attachment-download.md](references/attachment-download.md) — Load when you need attachment list/read/download/upload/delete workflows.
- [references/create-issue.md](references/create-issue.md) — Load before creating a Jira issue.
- [references/edit-issue.md](references/edit-issue.md) — Load before editing a Jira issue.
- [references/comment-on-issue.md](references/comment-on-issue.md) — Load before adding, updating, or deleting Jira comments.
- [references/link-issues.md](references/link-issues.md) — Load before listing, adding, or deleting Jira issue links.

## Mandatory Skill/CLI Alignment Rule

Any future change to `skills/jira2cli`, `packages/jira2cli/src/jira2cli/cli.py`, `packages/jira2cli/src/jira2cli/commands/*.py`, or `packages/jira2cli/README.md` must verify that this skill still matches the current CLI.

Required verification:

- compare this skill against `packages/jira2cli/src/jira2cli/cli.py`
- compare this skill against `packages/jira2cli/src/jira2cli/commands/*.py`
- compare this skill against `packages/jira2cli/README.md`
- as a maintainer source check, verify commands and options against current local help output from `uv run --locked --package jira2cli jira2cli --help`
- verify any documented command-specific options against that command's `--help`

If the skill text and the CLI/help output disagree, fix or qualify the docs before proceeding.

## Authentication and launch

Supported credential modes:

- `uvx jira2cli --credentials-file <path> ...`
- environment variables `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` when `--credentials-file` is omitted

There is **no** default credentials path and **no** implicit `JIRA_CREDENTIALS_FILE` behavior.

Credentials file shape:

```json
{
  "url": "https://<site>.atlassian.net",
  "username": "<email>",
  "api_token": "<api-token>"
}
```

## Common Safety Rules

- Use `uvx jira2cli ...` for consumer CLI commands.
- UVX runs the CLI but does not install or auto-discover the Pi skill; load this source-checkout skill explicitly when needed.
- For repository contributor or maintainer checks after workspace setup, use `uv run --locked --package jira2cli jira2cli ...`.
- Never print `JIRA_API_TOKEN` or other secrets.
- Do not guess project keys, issue types, user identities, required Jira fields, attachment IDs, comment IDs, worklog IDs, transition names, saved filter IDs, or link direction.
- Before create, edit, transition, comment, comment-update, comment-delete, link, delete-link, attachment, attachment-upload, attachment-delete, worklog-add, worklog-update, or worklog-delete actions, gather the relevant issue state or metadata first. For transitions, read the current issue first, then use fresh structured transition metadata before choosing an action.
- Before mutating Jira, summarize the intended action, the exact field choices or IDs, and ask the user to confirm.
- Prefer `--json` for structured reads and structured mutation confirmations.
- Use `--raw` only when you need API-oriented output on commands that support it. `read` does not support `--raw`; use `read --json` for its unchanged Jira response. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes. Do not pass `--raw` and `--json` together on commands that support both.
- `read` requires exactly one `--fields FIELD[,FIELD...]` option. CSV segments are trimmed, must be non-empty, and are forwarded in order as Jira field keys, IDs, or endpoint-supported selectors. `--json` bypasses formatting and preserves raw Jira data, including ADF. Wildcard and negative selectors can still return broad responses.
- Unlike singular `read`, `search` and `filter-run` are multi-issue projected reads: one invocation returns one page, and requested `--fields` apply to every issue in it. Fields may still be absent or null. `filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.
- For `search` and `filter-run`, `--fields` is optional and may appear at most once as comma-delimited selectors (`--fields key,summary`). If omitted, fields default to `summary, status, assignee, priority, issuetype, created, updated`. Projection is whole-field: `assignee` may include Jira-permitted nested identity, email, and avatar data; envelope metadata may remain. Plain output is the helper's fixed compact view; use structured `--json` or `--raw` and local `jq` reduction for arbitrary requested fields.
- `search` and `filter-run` return one page per invocation. `--max-results` is per-page (default 20, maximum 50). With structured output, continue only while the opaque `nextPageToken` is non-empty, forwarding it unchanged as `--next-page-token`; do not use `total` to decide. Keep the JQL (or saved filter), requested fields, and page size stable. Do not edit a saved filter during continuation. Atlassian expires each `nextPageToken` in seven days, so complete pagination within that window; if it expires, rerun the search or filter from the first page.
- For known issue keys, use JQL `key IN (...)`; split a large key list into batches if Jira rejects the query. An embedded `comment` or `worklog` field may be partial; use the dedicated paginated `comments <KEY>` or `worklogs <KEY>` commands for complete collections.
- `fields-list` returns one Jira field-catalog page. It accepts optional `--project-key`, `--query`, canonical `--field-ids`, `--field-types system[,custom]`, `--start-at` (default 0), and `--max-results` (default 20). The project key is only Jira project context/access filtering; it does not establish issue-type, Create-screen, or Edit-screen applicability. Jira documents the endpoint for classic projects. Continue with the same filters using returned `startAt + len(values)`; use `fields` for create/edit metadata.
- `changelogs <KEY>` fetches every Jira GET page before returning complete history. Optional `--created-at-or-after`, `--created-before`, and canonical `--field-ids` filters are applied locally; field filtering exactly matches raw `fieldId` and drops emptied events. `--result-max-results` optionally pages retained events locally after complete retrieval; nonzero `--result-start-at` requires it. Use `changelogs-by-ids <KEY> --changelog-ids ID[,ID...]` only for known IDs: it uses Jira's distinct POST endpoint and accepts the same `--field-ids` filter, but no result pagination. The one required plural changelog-ID CSV option is trimmed, requires non-empty base-10 integer segments, and preserves order and duplicates. Both `--json` and `--raw` return normalized helper-owned structured output rather than untouched HTTP output; full histories may be large or externally clipped.
- Transition workflow: read current `summary,status` and fields expected to change; run `transitions <KEY> --json` for expanded structured metadata and use `--include-unavailable` only for diagnostics or `--transition-id <ACTION_ID>` to focus it. Prefer a freshly discovered **transition action ID**, not a destination status ID. Inspect availability, screen/conditional/global/looped indicators, required/schema/operations/allowed/default/autocomplete/configuration, then make one `transition <KEY> <ACTION_ID> --fields-json '<OBJECT>' --update-json '<OBJECT>' --json` request as needed. Each JSON option must be an object and is forwarded as native Jira data: no Markdown/ADF conversion, comment/worklog convenience flags, automatic verification, or retry. Native `update.comment` bodies must already be Jira-native ADF. Never use the exact same field key in `fields` and `update`. Jira can accept with `204 No Content` and return no issue; reread status and changed fields, then inspect comments/worklogs or changelog when relevant. Reconcile a `400` (including a configured account that lacks permission to transition the issue), `409`, timeout, or `5xx` by rereading current issue/metadata first; do not blindly retry non-idempotent transitions or native operations. Inline JSON can enter shell history, and Jira data is not secret storage.

## Flat command surface

### Identity

- `auth-status`
- `me`

### Reads, changelog history, search, and transitions

- `read`
- `comments`
- `changelogs`
- `changelogs-by-ids`
- `search`
- `transitions`
- `transition`

### Metadata and saved filters

- `fields`
- `fields-list`
- `project`
- `projects`
- `statuses`
- `priorities`
- `users`
- `link-types`
- `jql-syntax`
- `filters`
- `filter-run`

### Issue mutations and links

- `create`
- `edit`
- `comment`
- `comment-update`
- `comment-delete`
- `issue-links`
- `add-link`
- `delete-link`

### Attachments and worklogs

- `attachment`
- `attachment-list`
- `attachment-read`
- `attachment-download`
- `attachment-upload`
- `attachment-delete`
- `worklogs`
- `worklog-add`
- `worklog-update`
- `worklog-delete`
- `worklog-report`

## Common commands

- `uvx jira2cli --help`
- `uvx jira2cli auth-status`
- `uvx jira2cli --credentials-file <path> me --json`
- `uvx jira2cli projects --query <text> --json`
- `uvx jira2cli fields --project-key <PROJECT> --json`
- `uvx jira2cli fields-list --project-key <PROJECT> --field-types system --start-at <N> --max-results <N> --json`
- `uvx jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
- `uvx jira2cli fields --issue-key <KEY> --json`
- `uvx jira2cli users <query> --max-results <N> --json`
- `uvx jira2cli jql-syntax`
- `uvx jira2cli search '<JQL>' --fields key,summary,status --max-results <N> --next-page-token '<TOKEN>' --json`
- `uvx jira2cli read <KEY> --fields summary,<FIELD_ID> --json`
- `uvx jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
- `uvx jira2cli changelogs <KEY> --field-ids <FIELD_ID[,FIELD_ID...]> --result-start-at <N> --result-max-results <N> --json`
- `uvx jira2cli changelogs-by-ids <KEY> --changelog-ids <ID[,ID...]> --field-ids <FIELD_ID[,FIELD_ID...]> --json`
- `uvx jira2cli transitions <KEY> --json`
- `uvx jira2cli transitions <KEY> --include-unavailable --json` — diagnostic only for blocked or absent actions
- `uvx jira2cli transitions <KEY> --transition-id <ACTION_ID> --json`
- `uvx jira2cli transition <KEY> <ACTION_ID> --fields-json '<OBJECT>' --update-json '<OBJECT>' --json`
- `uvx jira2cli filters --query <text> --json`
- `uvx jira2cli filter-run <FILTER_ID> --fields key,summary --max-results <N> --next-page-token '<TOKEN>' --json`
- `uvx jira2cli worklogs <KEY> --json`
- `uvx jira2cli worklog-add <KEY> '1h 30m' --comment <text> --json`
- `uvx jira2cli worklog-update <KEY> <WORKLOG_ID> --time-spent '45m' --json`
- `uvx jira2cli worklog-delete <KEY> <WORKLOG_ID> --json`
- `uvx jira2cli worklog-report --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --jql '<JQL>' --account-id <ACCOUNT_ID> --max-issues <N> --include-details --json`
- `uvx jira2cli attachment <ATTACHMENT_ID> --output-path <path>`
- `uvx jira2cli attachment-list <KEY> --json`
- `uvx jira2cli attachment-read <ATTACHMENT_ID> --json`
- `uvx jira2cli attachment-download <ATTACHMENT_ID> --output-path <path> --json`
- `uvx jira2cli attachment-upload <KEY> <PATH> --json`
- `uvx jira2cli attachment-delete <ATTACHMENT_ID> --json`
- `uvx jira2cli create <PROJECT> <TYPE> <SUMMARY> --description <text> --fields-json '<json>' --json`
- `uvx jira2cli edit <KEY> --summary <text> --description <text> --fields-json '<json>' --json`
- `uvx jira2cli comment <KEY> <BODY> --json`
- `uvx jira2cli comment-update <KEY> <COMMENT_ID> <BODY> --json`
- `uvx jira2cli comment-delete <KEY> <COMMENT_ID> --json`
- `uvx jira2cli issue-links <KEY> --json`
- `uvx jira2cli link-types --json`
- `uvx jira2cli add-link <LINK_TYPE> <OUTWARD_KEY> <INWARD_KEY> --json`
- `uvx jira2cli delete-link <LINK_ID> --json`
