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

For a local CLI instead, see the [jira2cli guide](https://github.com/en-ver/jira2ai/blob/main/packages/jira2cli/README.md). Contribution and maintainer guidance is in the [repository contributing guide](https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md).

## License

MIT
