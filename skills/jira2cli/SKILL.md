---
name: jira2cli
description: Jira Cloud workflows through local `jira2cli` in this repo. Use when verifying `jira2cli`, discovering Jira metadata, reading issues/comments/worklogs, working with saved filters and transitions, downloading/uploading attachments, or safely mutating Jira issues.
---

# jira2cli

Use `jira2cli` for Jira Cloud workflows from a local checkout of this repository.

`jira2cli` is **Jira Cloud only**. Do not treat it as Jira Server/Data Center support.

It also does **not** provide dedicated issue assign commands, issue delete/archive flows, sprint/board/epic operations, or admin-heavy Jira configuration tooling.

## References

- [references/install-auth.md](references/install-auth.md) — Load when you need the supported local/dev command prefix, CLI verification, or Jira auth setup.
- [references/project-discovery.md](references/project-discovery.md) — Load when you need to resolve the right Jira project key or discover issue types with `fields --project-key`.
- [references/field-metadata.md](references/field-metadata.md) — Load before create/edit work when you need required fields, editable fields, or allowed values.
- [references/user-identity-lookup.md](references/user-identity-lookup.md) — Load when a Jira user field needs an `accountId` or exact display name.
- [references/jql-syntax.md](references/jql-syntax.md) — Load when composing or debugging JQL.
- [references/search-and-read-issues.md](references/search-and-read-issues.md) — Load when you need to search issues, read details, request extra fields, or page through comments.
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
- verify commands and options against current help output from `uv run --locked jira2cli --help`
- verify any documented command-specific options against that command's `--help`

If the skill text and the CLI/help output disagree, fix or qualify the docs before proceeding.

## Authentication and launch

Supported credential modes:

- `uv run jira2cli --credentials-file <path> ...`
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

- This repo currently supports local/dev `jira2cli` usage from the workspace root: `uv run jira2cli ...`.
- `--package jira2cli` is optional advanced workspace-member selection, not the normal local command form.
- Do not claim `uvx jira2cli`, PyPI install, or wheel auto-discovery support unless the repo docs and CLI release flow are updated first.
- Never print `JIRA_API_TOKEN` or other secrets.
- Do not guess project keys, issue types, user identities, required Jira fields, attachment IDs, comment IDs, worklog IDs, transition names, saved filter IDs, or link direction.
- Before create, edit, transition, comment, comment-update, comment-delete, link, delete-link, attachment, attachment-upload, attachment-delete, worklog-add, worklog-update, or worklog-delete actions, gather the relevant issue state or metadata first.
- Before mutating Jira, summarize the intended action, the exact field choices or IDs, and ask the user to confirm.
- Prefer `--json` for structured reads and structured mutation confirmations.
- Use `--raw` only when you need the untouched API payload, and do not pass `--raw` and `--json` together.
- `filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.

## Flat command surface

### Identity

- `auth-status`
- `me`

### Reads, search, and transitions

- `read`
- `comments`
- `search`
- `transitions`
- `transition`

### Metadata and saved filters

- `fields`
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

- `uv run --locked jira2cli --help`
- `uv run jira2cli auth-status`
- `uv run jira2cli --credentials-file <path> me --json`
- `uv run jira2cli projects --query <text> --json`
- `uv run jira2cli fields --project-key <PROJECT> --json`
- `uv run jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
- `uv run jira2cli fields --issue-key <KEY> --json`
- `uv run jira2cli users <query> --max-results <N> --json`
- `uv run jira2cli jql-syntax`
- `uv run jira2cli search '<JQL>' --field key --field summary --field status --max-results <N> --json`
- `uv run jira2cli read <KEY> --extra-field <FIELD_ID> --json`
- `uv run jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
- `uv run jira2cli transitions <KEY> --json`
- `uv run jira2cli transition <KEY> <TRANSITION_ID_OR_NAME> --json`
- `uv run jira2cli filters --query <text> --json`
- `uv run jira2cli filter-run <FILTER_ID> --field key --field summary --json`
- `uv run jira2cli worklogs <KEY> --json`
- `uv run jira2cli worklog-add <KEY> '1h 30m' --comment <text> --json`
- `uv run jira2cli worklog-update <KEY> <WORKLOG_ID> --time-spent '45m' --json`
- `uv run jira2cli worklog-delete <KEY> <WORKLOG_ID> --json`
- `uv run jira2cli worklog-report --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --jql '<JQL>' --account-id <ACCOUNT_ID> --max-issues <N> --include-details --json`
- `uv run jira2cli attachment <ATTACHMENT_ID> --output-path <path>`
- `uv run jira2cli attachment-list <KEY> --json`
- `uv run jira2cli attachment-read <ATTACHMENT_ID> --json`
- `uv run jira2cli attachment-download <ATTACHMENT_ID> --output-path <path> --json`
- `uv run jira2cli attachment-upload <KEY> <PATH> --json`
- `uv run jira2cli attachment-delete <ATTACHMENT_ID> --json`
- `uv run jira2cli create <PROJECT> <TYPE> <SUMMARY> --description <text> --fields-json '<json>' --json`
- `uv run jira2cli edit <KEY> --summary <text> --description <text> --fields-json '<json>' --json`
- `uv run jira2cli comment <KEY> <BODY> --json`
- `uv run jira2cli comment-update <KEY> <COMMENT_ID> <BODY> --json`
- `uv run jira2cli comment-delete <KEY> <COMMENT_ID> --json`
- `uv run jira2cli issue-links <KEY> --json`
- `uv run jira2cli link-types --json`
- `uv run jira2cli add-link <LINK_TYPE> <OUTWARD_KEY> <INWARD_KEY> --json`
- `uv run jira2cli delete-link <LINK_ID> --json`
