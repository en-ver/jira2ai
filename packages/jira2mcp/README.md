# jira2mcp

A published stdio MCP server for **Jira Cloud**. Requires Python 3.13+.

Use `jira2mcp` with any MCP client that can launch a stdio server. It does not support Jira Server or Data Center, and does not provide dedicated issue assignment, issue delete/archive, sprint/board/epic, or admin-configuration operations.

## Install and configure

Install [uv](https://docs.astral.sh/uv/), then configure your MCP client to start the server:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": ["jira2mcp"]
    }
  }
}
```

For Claude Code:

```bash
claude mcp add jira -- uvx jira2mcp
```

The server uses stdio. Its only launch option is:

```text
--credentials-file PATH  Explicit path to a Jira Cloud JSON credentials file
```

For example:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": ["jira2mcp", "--credentials-file", "~/.config/jira-cloud.json"]
    }
  }
}
```

## Authentication

Set environment credentials:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

Or pass an explicit file, which takes precedence over environment credentials:

```json
{
  "url": "https://yourcompany.atlassian.net",
  "username": "you@company.com",
  "api_token": "your-api-token"
}
```

There is no default credentials-file path and no `JIRA_CREDENTIALS_FILE` environment variable. Create a token in your [Atlassian account](https://id.atlassian.com/manage-profile/security/api-tokens); never commit, print, or expose it in prompts or shared configuration.

## Tools

All tools use the `jira_*` namespace.

### Identity, reads, and transitions

| Tool | Description |
|---|---|
| `jira_auth_status` | Check configured credentials. |
| `jira_me` | Show the authenticated Jira user. |
| `jira_read` | Read explicitly requested issue fields as raw structured data. |
| `jira_search` | Search issues with JQL. |
| `jira_comments` | List issue comments. |
| `jira_changelogs` | Retrieve complete issue changelog history, with optional local timestamp filtering. |
| `jira_changelogs_by_ids` | Retrieve entries for known changelog IDs through Jira's distinct POST endpoint. |
| `jira_transitions` | List available issue transitions. |
| `jira_transition` | Apply an explicit transition. |

### Metadata and saved filters

| Tool | Description |
|---|---|
| `jira_fields` | Get create/edit field metadata. |
| `jira_list_fields` | Return one searchable Jira field catalog page. |
| `jira_projects` / `jira_project` | List projects or read one by key or ID. |
| `jira_users` | Search users by name or email. |
| `jira_statuses` / `jira_priorities` | List visible statuses or priorities. |
| `jira_filters` | List or search visible saved filters. |
| `jira_run_filter` | Resolve a saved filter's JQL and search with it. |

### Issues, comments, and links

| Tool | Description |
|---|---|
| `jira_create` / `jira_edit` | Create or update an issue. |
| `jira_comment` / `jira_update_comment` / `jira_delete_comment` | Add, update, or delete a comment. |
| `jira_issue_links` | List links on an issue. |
| `jira_add_link` / `jira_delete_link` | Create or delete an issue link. |

### Attachments and worklogs

| Tool | Description |
|---|---|
| `jira_attachment` | Download an attachment with the original simple surface. |
| `jira_attachments` / `jira_attachment_metadata` | List attachments or read metadata. |
| `jira_download_attachment` / `jira_upload_attachment` / `jira_delete_attachment` | Download, upload, or delete an attachment. |
| `jira_worklogs` | List issue worklogs. |
| `jira_add_worklog` / `jira_update_worklog` / `jira_delete_worklog` | Add, update, or delete a worklog. |
| `jira_worklog_report` | Report worklogs for JQL-selected issues in a UTC date range. |

The server also provides the `data://jira/link-types` resource and the `jira_jql_syntax` prompt.

## Usage and safety

High-level Markdown writes—issue descriptions, compatible rich-text field strings, comment add/update bodies, and worklog add/update comments—recognize the canonical Jira mention `[~accountId:<id>]` and convert it to one semantic ADF mention. Escaped, malformed, code, link, and image forms remain text. Jira may notify the referenced account. Native `jira_transition` `fields` and `update` data is not converted.

Formatted issue, comment, and worklog Markdown is presentation-only and may lose mention identity when edited or written back. For identity-safe edits, preserve raw ADF from `jira_read` structured data for issue fields and `raw=True` `jira_comments` or `jira_worklogs` results for their bodies; do not write formatted text back when mention identity matters.

`jira_read` returns selected Jira fields unchanged, including ADF, as structured content and a compact JSON text fallback; it does not format or truncate the response. `jira_run_filter` returns the same search-shaped result as `jira_search` after resolving the filter's JQL. `jira_download_attachment` provides structured/raw-friendly output, while `jira_attachment` remains available for its original simple download surface.

`jira_read` requires both `issue_key` and a non-empty native `fields` array, for example `jira_read(issue_key="PROJ-123", fields=["summary", "description"])`. Each array item is one field key, ID, or endpoint-supported selector; do not use comma-separated items or surrounding whitespace. It has no `raw` mode because it always returns structured Jira data. Selectors such as `*all`, `*navigable`, or negative selectors can still return broad responses, so request only what is needed.

Before a create or edit, call `jira_fields` for the target project and issue type. Before a transition, link, comment update/delete, attachment deletion, or worklog mutation, read the current state and use exact IDs or names. Attachment uploads must stay within the server working directory. Downloads must stay within advertised MCP roots, or the server working directory when roots are unavailable. All reads and writes remain subject to the configured Jira account's permissions.

### Workflow transitions

A transition action is a current workflow action, not a status update. Read the current issue first, including `status` and fields expected to change. Then use structured expanded metadata, normally with `raw=True`, and prefer a newly discovered action ID:

```text
jira_read(issue_key="PROJ-123", fields=["summary", "status", "resolution"])
jira_transitions(issue_key="PROJ-123", raw=True)
# Diagnostic only when investigating a blocked or absent action.
jira_transitions(issue_key="PROJ-123", include_unavailable_transitions=True, raw=True)
jira_transitions(issue_key="PROJ-123", transition_id="31", raw=True)
```

`transition_id="31"` identifies the transition action ID; it is not the destination status ID. Inspect availability, screen/conditional/global/looped indicators, required fields, schema, operations, allowed values, defaults, autocomplete, and configuration before one request. A looped action can intentionally retain the same status. `include_unavailable_transitions=True` is diagnostic only: never submit an unavailable action.

`jira_transition` accepts one native Jira `fields` object and/or `update` object. It forwards those JSON shapes unchanged: it does not expose helper history/entity properties, convert Markdown to ADF, add comment/worklog convenience parameters, locally validate screen values, automatically verify, or guarantee ACID/idempotent behavior. Do not place an exact field key in both `fields` and `update`; `jira2py` rejects that overlap before posting.

```text
jira_transition(
  issue_key="PROJ-123",
  transition="31",
  fields={"resolution": {"name": "Done"}}
)

# Use only when the discovered operations permit a native comment add.
jira_transition(
  issue_key="PROJ-123",
  transition="31",
  update={"comment": [{"add": {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Approved for release."}]}]}}}]}
)

# A native worklog add is likewise conditional on the discovered operations.
jira_transition(
  issue_key="PROJ-123",
  transition="31",
  update={"worklog": [{"add": {"timeSpent": "30m", "comment": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Release verification"}]}]}}}]}
)
```

Native `jira_transition.update` comment bodies must already be Jira-native ADF; the worklog bodies above are likewise ADF, and the `update` values are native operation arrays. Jira data is persistent and is not secret storage; never put credentials or secrets in transition fields, comments, or worklogs.

Jira commonly replies `204 No Content`, so acceptance returns no issue object and is not verification. Reread the status and changed fields; inspect comments, worklogs, or changelog when relevant. For a `400`, revisit the fresh metadata, screen, required/schema/allowed values, and operation shape, or determine whether the configured account lacks permission to transition the issue. For a `409`, timeout, or `5xx`, delivery or final state can be uncertain: reread first, then decide on one new request. Do **not** blindly retry a transition or native comment/worklog update because it can be non-idempotent.

### Field catalog

`jira_list_fields` returns exactly one Jira `/field/search` page. Its `start_at` default is `0`, `max_results` default is `20`, and it accepts optional `project_key`, `query`, native `field_ids` arrays, and `field_types` arrays containing `"system"` and/or `"custom"`. Normal text is concise (field name and canonical ID). With `raw=True`, it returns the complete Jira page envelope, including `values`, `startAt`, `maxResults`, `total`, `isLast`, and any other Jira properties as structured content and a JSON text fallback.

To continue, retain every filter and use `startAt + len(values)` as the next `start_at`; stop when Jira reports `isLast`. Jira can cap the requested page size, so use its returned metadata. The endpoint is documented for classic projects. `project_key` only supplies Jira project context/access filtering: it does **not** identify fields applicable to an issue type, Create screen, or Edit screen. Use `jira_fields` for issue-type, create-screen, and edit-screen metadata.

### Changelog history

`jira_changelogs` retrieves every Jira GET page for an issue before returning one helper-owned structured envelope, `{"issue_key": "<KEY>", "changelogs": [...]}`. Its optional timestamp bounds are client-side filters applied after complete retrieval with `created_at_or_after <= created < created_before`; they do not limit Jira's GET requests. Its optional native `field_ids` array retains only changelog items whose raw `fieldId` exactly matches a canonical field ID, dropping history events with no retained items.

`jira_changelogs` normally returns every retained event. Supplying `result_max_results` enables local event pagination; `result_start_at` defaults to `0` and requires `result_max_results` when nonzero. Jira's complete history is still fetched before timestamp and field-ID filters and the result slice. Paged raw output adds helper-owned `result_page` metadata; it is not Jira server pagination.

Use `jira_changelogs_by_ids` only for IDs already known from that history. It uses Jira's distinct known-ID POST endpoint and accepts the same native `field_ids` array filter. Jira controls the returned order. This known-ID operation has no result pagination, so request fewer IDs when a smaller response is needed.

Normal text is condensed and server-truncated at 30,000 characters. With `raw=True`, both changelog tools return the untruncated helper-owned envelope as MCP structured content plus JSON text fallback, not untouched API pages. Complete histories and raw results may be large and can still be clipped by an MCP client or harness.

### Search pagination and raw output

Each `jira_search` or `jira_run_filter` invocation returns exactly one issue page; `jira_search` fetches one issue page, while `jira_run_filter` resolves its saved filter and then fetches one issue page. `max_results` is per page, defaults to `20`, and is capped at `50`. To continue, pass the non-empty response `nextPageToken` as the next request's `next_page_token`; the names intentionally differ. Keep the same JQL (or saved filter ID), `fields`, and page size for every call. For example:

```text
jira_search(jql="project = PROJ", max_results=20, fields=["summary"], raw=True)
jira_search(jql="project = PROJ", max_results=20, fields=["summary"], next_page_token="<nextPageToken>", raw=True)
```

Use `raw=True` from the first page. Raw mode returns the complete API-shaped page as both MCP structured content and a JSON text fallback, including `nextPageToken` and arbitrary requested fields. Normal formatted text has a fixed issue view and is server-truncated at 30,000 characters; raw mode is not server-truncated, but an MCP client or harness can still clip its result. If a current page was externally clipped, continuing with its token can skip issues that were not displayed.

Field selection is whole-field projection, not nested projection or redaction. Omitting `fields` requests all seven defaults: `summary`, `status`, `assignee`, `priority`, `issuetype`, `created`, and `updated`. In particular, `assignee` can include nested identity, email, and avatar data allowed by the Jira account. Request explicit fields when that data is not wanted. Arbitrary fields are available in raw mode; normal formatted text remains the fixed issue view.

Continue whenever `nextPageToken` is non-empty, including when an intermediate page has no issues. Stop only when the token is absent or empty, not when `total` is reached or reported. Tokens expire after seven days; restart from the first page when one expires. `jira_run_filter` resolves the saved filter on every call, so do not edit the filter while paging. Jira result-set changes, including a changed saved filter, can otherwise produce duplicates or omissions.

For the published Jira CLI, see the [jira2cli guide](https://github.com/en-ver/jira2ai/blob/main/packages/jira2cli/README.md). Contribution and maintainer guidance is in the [repository contributing guide](https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md).

## License

MIT
