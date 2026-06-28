# jira2cli

Flat CLI adapter for **Jira Cloud only**, powered by `jira2py` helpers.

`jira2cli` is currently intended for local and development use from this workspace. Do not assume a published `uvx jira2cli` or PyPI install path yet.

`jira2cli` does **not** target Jira Server/Data Center. It also does not add dedicated issue assign commands, issue delete/archive flows, sprint/board/epic operations, or admin-heavy Jira configuration tooling.

## Authentication

`jira2cli` supports two explicit credential modes:

1. `--credentials-file <path>` on the CLI
2. `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` environment variables when the flag is omitted

Optional explicit credentials file format:

```json
{
  "url": "https://yourcompany.atlassian.net",
  "username": "you@company.com",
  "api_token": "your-api-token"
}
```

If `--credentials-file` is omitted, `jira2cli` uses environment variables.

There is **no** default credentials path and **no** implicit `JIRA_CREDENTIALS_FILE` behavior.

Environment variable example:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

## Local usage

From the workspace root:

```bash
uv sync --all-packages --group dev
uv run jira2cli --help
uv run jira2cli auth-status
uv run jira2cli --credentials-file ~/.config/jira-cloud.json me --json
uv run jira2cli read PROJ-123
uv run jira2cli transitions PROJ-123 --json
uv run jira2cli filter-run 10400 --field key --field summary --json
```

Use `uv run --package jira2cli jira2cli ...` only when you want explicit advanced workspace-member selection.

## Command surface

### Identity

| Command | Description |
|---|---|
| `auth-status` | Check whether the configured Jira Cloud credentials authenticate |
| `me` | Show the currently authenticated Jira Cloud user |

### Reads, search, and transitions

| Command | Description |
|---|---|
| `read` | Read a Jira issue by key with full details |
| `comments` | List comments on an issue |
| `search` | Search issues using JQL |
| `transitions` | List available workflow transitions for an issue |
| `transition` | Apply a workflow transition to an issue |

### Metadata and saved filters

| Command | Description |
|---|---|
| `fields` | Get field metadata for create/edit workflows |
| `project` | Read one project by key or ID |
| `projects` | List accessible projects |
| `statuses` | List visible Jira statuses |
| `priorities` | List visible Jira priorities |
| `users` | Search users by name or email |
| `link-types` | List available Jira issue link types |
| `jql-syntax` | Print the shared JQL syntax reference |
| `filters` | List or search saved filters visible to the current user |
| `filter-run` | Resolve a saved filter's JQL and run the normal search flow |

### Issue mutations and links

| Command | Description |
|---|---|
| `create` | Create a new issue |
| `edit` | Update an existing issue |
| `comment` | Add a comment to an issue |
| `comment-update` | Update an existing issue comment |
| `comment-delete` | Delete an issue comment |
| `issue-links` | List issue links on a specific issue |
| `add-link` | Create a link between two issues |
| `delete-link` | Delete an issue link |

### Attachments and worklogs

| Command | Description |
|---|---|
| `attachment` | Download an attachment with the original simple surface |
| `attachment-list` | List attachments on an issue |
| `attachment-read` | Read attachment metadata by ID |
| `attachment-download` | Download an attachment with structured/raw output support |
| `attachment-upload` | Upload a local file as an issue attachment |
| `attachment-delete` | Delete an attachment by ID |
| `worklogs` | List worklogs on an issue |
| `worklog-add` | Add a worklog to an issue |
| `worklog-update` | Update an existing worklog |
| `worklog-delete` | Delete a worklog |
| `worklog-report` | Build a worklog report for JQL-selected issues within a UTC date range |

## Output modes

Most structured commands support:

- `--json` for structured helper output
- `--raw` for the untouched API payload

Do not pass `--json` and `--raw` together.

`filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.

## Worklog reports

Use `jira2cli worklog-report` to build a report for issues selected by JQL.

- Required options: `--start-date`, `--end-date`, and `--jql`
- Optional options: `--account-id`, `--max-issues`, `--include-details`, `--json`, and `--raw`
- Issue selection is JQL-only. For a single issue, use `--jql 'issue = PROJ-123'`
- Dates are interpreted in UTC, and `--end-date` is inclusive
- `--account-id` filters returned worklogs client-side by author `accountId`
- `--max-issues` defaults to `100`, must be at least `1`, and limits how many JQL-matched issues are scanned; the report notes truncation when more issues match
- Output rows use `displayName` as the friendly user name
- Results depend on the configured Jira account's issue/worklog visibility and permissions

## Pi skill reference

The Pi skill reference lives at repo-root `skills/jira2cli/`.

It is CLI-only, not a `jira2mcp`/MCP skill, and documents metadata-first Jira workflows plus safety rules for agents using `jira2cli`.

Consumers can use it as a reference/template for building their own Pi or agent skills. Load it from a local source checkout via an explicit skill path, for example:

```json
{
  "skills": ["/Users/enver/github/personal/jira2ai/skills/jira2cli"]
}
```

Do not assume Pi auto-discovers this skill from a Python wheel, PyPI install, or `uvx` install.

## Workspace layout

- `packages/jira2mcp` — MCP adapter published as `jira2mcp`
- `packages/jira2cli` — CLI adapter package

For MCP installs and Claude setup, use `uvx jira2mcp` and `claude mcp add jira -- uvx jira2mcp` as documented in the repository root README.

## Maintainers

Do not assume `uvx jira2cli` or `pip install jira2cli` is available yet. Keep using local workspace commands until the release gates in the maintainer docs are completed.

Release sequencing, package tags, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2ai/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md>
