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
| `jira_read` | Read an issue by key. |
| `jira_search` | Search issues with JQL. |
| `jira_comments` | List issue comments. |
| `jira_transitions` | List available issue transitions. |
| `jira_transition` | Apply an explicit transition. |

### Metadata and saved filters

| Tool | Description |
|---|---|
| `jira_fields` | Get create/edit field metadata. |
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

Descriptions and comments accept Markdown and are converted to Atlassian Document Format (ADF); rich-text Jira fields are returned as Markdown. `jira_run_filter` returns the same search-shaped result as `jira_search` after resolving the filter's JQL. `jira_download_attachment` provides structured/raw-friendly output, while `jira_attachment` remains available for its original simple download surface.

Before a create or edit, call `jira_fields` for the target project and issue type. Before a transition, link, comment update/delete, attachment deletion, or worklog mutation, read the current state and use exact IDs or names. Attachment uploads must stay within the server working directory. Downloads must stay within advertised MCP roots, or the server working directory when roots are unavailable. All reads and writes remain subject to the configured Jira account's permissions.

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
