# jira2mcp

MCP server for **Jira Cloud only**.

`jira2mcp` does **not** target Jira Server/Data Center. It also does not add dedicated issue assign commands, issue delete/archive flows, sprint/board/epic operations, or admin-heavy Jira configuration tooling.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [jira2py](https://pypi.org/project/jira2py/).

## Setup

### 1. Get your Jira Cloud credentials

You need three values from your Jira Cloud instance:

| Variable | Description |
|---|---|
| `JIRA_URL` | Your Jira instance URL (for example `https://yourcompany.atlassian.net`) |
| `JIRA_USER` | Your Jira account email |
| `JIRA_API_TOKEN` | API token from [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

Optional explicit credentials file format:

```json
{
  "url": "https://yourcompany.atlassian.net",
  "username": "you@company.com",
  "api_token": "your-api-token"
}
```

### 2. Install uv (if not already installed)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Add to Claude Code

```bash
claude mcp add jira -- uvx jira2mcp
```

### 4. Configure credentials

**Option A: environment variables**

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

Minimal MCP config:

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

You can also place the same values in the MCP `env` block.

**Option B: explicit credentials file launch argument**

```bash
claude mcp add jira -- uvx jira2mcp --credentials-file ~/.config/jira-cloud.json
```

Equivalent config:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": [
        "jira2mcp",
        "--credentials-file",
        "/Users/you/.config/jira-cloud.json"
      ]
    }
  }
}
```

If `--credentials-file` is omitted, `jira2mcp` uses `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` from the environment.

There is **no** default credentials path and **no** implicit `JIRA_CREDENTIALS_FILE` behavior.

## Tool inventory

### Identity, reads, and transitions

| Tool | Description |
|---|---|
| `jira_auth_status` | Check whether the configured Jira Cloud credentials authenticate |
| `jira_me` | Show the currently authenticated Jira Cloud user |
| `jira_read` | Read a Jira issue by key with full details |
| `jira_search` | Search issues using JQL |
| `jira_comments` | List comments on an issue |
| `jira_transitions` | List available workflow transitions for an issue |
| `jira_transition` | Apply a workflow transition to an issue |

### Metadata and saved filters

| Tool | Description |
|---|---|
| `jira_fields` | Get field metadata for create/edit workflows |
| `jira_projects` | List accessible projects |
| `jira_project` | Read one project by key or ID |
| `jira_users` | Search users by name or email |
| `jira_statuses` | List visible Jira statuses |
| `jira_priorities` | List visible Jira priorities |
| `jira_filters` | List or search saved filters visible to the current user |
| `jira_run_filter` | Resolve a saved filter's JQL and run the normal search flow |

### Issue mutations and links

| Tool | Description |
|---|---|
| `jira_create` | Create a new issue |
| `jira_edit` | Update an existing issue |
| `jira_comment` | Add a comment to an issue |
| `jira_update_comment` | Update an existing issue comment |
| `jira_delete_comment` | Delete an issue comment |
| `jira_issue_links` | List issue links on a specific issue |
| `jira_add_link` | Create a link between two issues |
| `jira_delete_link` | Delete an issue link |

### Attachments and worklogs

| Tool | Description |
|---|---|
| `jira_attachment` | Download an attachment with the original simple surface |
| `jira_attachments` | List attachments on an issue |
| `jira_attachment_metadata` | Read attachment metadata by ID |
| `jira_download_attachment` | Download an attachment with structured/raw output support |
| `jira_upload_attachment` | Upload a local file as an issue attachment |
| `jira_delete_attachment` | Delete an attachment by ID |
| `jira_worklogs` | List worklogs on an issue |
| `jira_add_worklog` | Add a worklog to an issue |
| `jira_update_worklog` | Update an existing worklog |
| `jira_delete_worklog` | Delete a worklog |
| `jira_worklog_report` | Build a worklog report for JQL-selected issues within a UTC date range |

## Resources

| Resource | Description |
|---|---|
| `data://jira/link-types` | Available issue link types in your Jira instance |

## Prompts

| Prompt | Description |
|---|---|
| `jql_syntax` | JQL syntax reference for building search queries |

## Notes

- `jira_run_filter` returns the same search-shaped result as `jira_search` after resolving the saved filter's JQL.
- `jira_attachment` remains available; `jira_download_attachment` adds structured/raw-friendly download output.
- Attachment upload support is Jira Cloud only and should use explicit local paths provided to the MCP server process.

## Key features

- Markdown descriptions and comments are converted to and from Atlassian Document Format (ADF).
- Field discovery via `jira_fields` keeps create/edit flows metadata-first.
- Saved filters, transitions, attachments, links, and worklogs are available through first-class MCP tools.

## Repository layout

This repository is a `uv` workspace with two packages:

- `packages/jira2mcp` — the FastMCP server/adapter package published as `jira2mcp`.
- `packages/jira2cli` — the CLI adapter package for local/dev use.

## Maintainers

`jira2mcp` releases are part of a multi-package workspace. Future tags use `jira2mcp-vX.Y.Z`, not broad `v*` tags.

See the maintainer release guide for sequencing, stop gates, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2ai/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md>

## License

MIT
