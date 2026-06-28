# jira2ai

Jira AI workspace for **Jira Cloud only** integrations.

This repo does **not** target Jira Server/Data Center. It also does not add dedicated issue assign commands, issue delete/archive flows, sprint/board/epic operations, or admin-heavy Jira configuration tooling.

This repository currently contains two packages:

- `jira2mcp` — the MCP adapter published as `jira2mcp`.
- `jira2cli` — a flat local/development CLI adapter.

Both packages are thin wrappers over published [jira2py](https://pypi.org/project/jira2py/) helpers.

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

**Option A: environment variables**

Export them in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

The MCP configuration can stay minimal:

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

You can also provide the same variables inline in the MCP `env` block instead of exporting them globally.

**Option B: explicit credentials file**

Pass the file explicitly to the MCP server:

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

## MCP tools

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

## CLI usage for local development

`jira2cli` is for local/development use in this workspace.

Sync the workspace once:

```bash
uv sync --all-packages --group dev
```

Use either environment variables or an explicit CLI flag:

```bash
uv run jira2cli auth-status
uv run jira2cli --credentials-file ~/.config/jira-cloud.json me --json
```

`uv run jira2cli ...` is the normal workspace-root form here. Use `uv run --package jira2cli jira2cli ...` only when you want explicit advanced workspace-member selection.

If `--credentials-file` is omitted, `jira2cli` uses `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` from the environment.

There is **no** default credentials path and **no** implicit `JIRA_CREDENTIALS_FILE` behavior.

### Flat `jira2cli` command surface

- Identity: `auth-status`, `me`
- Reads/search: `read`, `comments`, `search`, `transitions`, `transition`
- Metadata/reference: `fields`, `project`, `projects`, `statuses`, `priorities`, `users`, `link-types`, `jql-syntax`, `filters`, `filter-run`
- Issue mutations: `create`, `edit`, `comment`, `comment-update`, `comment-delete`
- Links: `issue-links`, `add-link`, `delete-link`
- Attachments: `attachment`, `attachment-list`, `attachment-read`, `attachment-download`, `attachment-upload`, `attachment-delete`
- Worklogs: `worklogs`, `worklog-add`, `worklog-update`, `worklog-delete`, `worklog-report`

`filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.

Representative commands:

```bash
uv run jira2cli --help
uv run jira2cli read PROJ-123
uv run jira2cli project PROJ --json
uv run jira2cli transitions PROJ-123 --json
uv run jira2cli filters --query mine --json
uv run jira2cli filter-run 10400 --field key --field summary --json
uv run jira2cli attachment-list PROJ-123 --json
uv run jira2cli worklogs PROJ-123 --json
uv run jira2cli worklog-report --start-date 2026-06-12 --end-date 2026-06-13 --jql 'issue = PROJ-123'
```

Continue to use `uvx jira2mcp` for MCP installs.

## Pi skill reference

A Pi skill reference lives at `skills/jira2cli/` in the repository root.

It is CLI-only and documents metadata-first Jira workflows and safety rules for agents using `jira2cli`; `jira2mcp`/MCP is out of scope for this skill.

Consumers can use it as a reference/template for building their own Pi or agent skills. Load it from a local source checkout via an explicit skill path, for example:

```json
{
  "skills": ["/Users/enver/github/personal/jira2ai/skills/jira2cli"]
}
```

Do not assume Pi auto-discovers this skill from a Python wheel, PyPI install, or `uvx` install.

## Key features

- **Markdown in, Markdown out** — descriptions and comments accept Markdown and are converted to Atlassian Document Format (ADF); rich-text Jira fields are converted back to Markdown.
- **Field discovery** — use `jira_fields` / `jira2cli fields` before create or edit operations.
- **Saved filter reuse** — use `jira_filters` / `jira2cli filters` to discover saved filters, then `jira_run_filter` / `jira2cli filter-run` to execute them through the standard search flow.
- **Attachment workflows** — list, inspect, download, upload, and delete attachments from MCP or the CLI.
- **Workflow transitions** — inspect transitions first, then apply an explicit transition ID or exact name.
- **Worklog workflows** — list, report, add, update, and delete worklogs with explicit issue/worklog IDs.

## Repository layout

This repository is a `uv` workspace with two packages:

- `packages/jira2mcp` — the FastMCP server/adapter package published as `jira2mcp`.
- `packages/jira2cli` — the CLI adapter package for local/dev use.
- `skills/jira2cli` — the repo-root CLI-only Pi skill reference/template for agents using `jira2cli`.

End-user MCP setup stays the same: use `uvx jira2mcp` directly or `claude mcp add jira -- uvx jira2mcp`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for workspace setup, development checks, pull request guidance, and maintainer release links.

## Maintainers

Package-specific release steps, tag formats, and current stop gates live in [docs/releasing.md](docs/releasing.md).

## License

MIT
