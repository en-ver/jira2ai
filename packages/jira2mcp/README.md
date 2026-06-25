# jira2mcp

MCP server for Jira Cloud — gives AI assistants like Claude the ability to read, create, edit, search, and comment on Jira issues.

This repository also contains `jira2cli` for local and development CLI usage.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [jira2py](https://pypi.org/project/jira2py/).

## Setup

### 1. Get your Jira credentials

You need three values from your Jira Cloud instance:

| Variable | Description |
|---|---|
| `JIRA_URL` | Your Jira instance URL (e.g. `https://yourcompany.atlassian.net`) |
| `JIRA_USER` | Your Jira account email |
| `JIRA_API_TOKEN` | API token from [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

### 2. Install uv (if not already installed)

`uvx` is part of [uv](https://docs.astral.sh/uv/), a fast Python package manager:

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

**Option A: Shell environment variables**

Export them in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

The MCP configuration stays minimal:

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

**Option B: Inline in MCP configuration**

If you prefer not to set global environment variables, provide them directly in the `env` section:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": ["jira2mcp"],
      "env": {
        "JIRA_URL": "https://yourcompany.atlassian.net",
        "JIRA_USER": "you@company.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `jira_read` | Read a Jira issue by key with full details |
| `jira_search` | Search issues using JQL |
| `jira_create` | Create a new issue |
| `jira_edit` | Update an existing issue |
| `jira_comment` | Add a comment to an issue |
| `jira_comments` | List comments with pagination |
| `jira_fields` | Get field metadata for create/edit screens |
| `jira_projects` | List accessible projects |
| `jira_users` | Search users by name or email |
| `jira_attachment` | Download an attachment |
| `jira_add_link` | Create a link between two issues |
| `jira_delete_link` | Delete an issue link |
| `jira_worklog_report` | Build a worklog report for JQL-selected issues within a UTC date range |

### `jira_worklog_report`

- Required parameters: `start_date`, `end_date`, and `jql`.
- Optional parameters: `account_id`, `max_issues`, `include_details`, and `raw`.
- Issue selection is JQL-only. For a single issue, use JQL such as `issue = PROJ-123`.
- Dates are interpreted in UTC, and `end_date` is inclusive.
- Optional `account_id` filtering is applied client-side by worklog author `accountId`.
- `max_issues` defaults to `100`, must be at least `1`, and limits how many JQL-matched issues are scanned; the report notes truncation when more issues match.
- Output rows use `displayName` as the friendly user name.
- Results depend on the configured Jira account's issue/worklog visibility and permissions.

## Resources

| Resource | Description |
|---|---|
| `data://jira/link-types` | Available issue link types in your Jira instance |

## Prompts

| Prompt | Description |
|---|---|
| `jql_syntax` | JQL syntax reference for building search queries |

## Key features

- **Markdown in, Markdown out** — write descriptions and comments in Markdown; they're auto-converted to Atlassian Document Format (ADF). ADF fields from Jira are converted back to Markdown.
- **Field discovery** — use `jira_fields` to discover required and available fields before creating or editing issues.
- **User lookup** — use `jira_users` to resolve display names to account IDs for assignment.
- **Extra fields** — request additional fields on `jira_read` beyond the standard set; rich-text fields are auto-converted.
- **Link management** — read the `data://jira/link-types` resource to discover available link types, then create or delete links between issues.

## Repository layout

This repository is a `uv` workspace with two packages:

- `packages/jira2mcp` — the FastMCP server/adapter package published as `jira2mcp`.
- `packages/jira2cli` — the CLI adapter package for local/dev use.

End-user MCP setup stays the same: use `uvx jira2mcp` directly or `claude mcp add jira -- uvx jira2mcp`.

## Maintainers

`jira2mcp` releases are part of a multi-package workspace. Future tags use `jira2mcp-vX.Y.Z`, not broad `v*` tags.

See the maintainer release guide for sequencing, stop gates, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2ai/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md>

## License

MIT
