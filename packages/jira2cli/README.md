# jira2cli

CLI adapter for Jira Cloud, powered by `jira2ai-core`.

`jira2cli` is currently intended for local and development use from this workspace. Do not assume a published `uvx` or PyPI install path yet.

## Environment

`jira2cli` uses the same Jira credentials as `jira2mcp`:

| Variable | Description |
|---|---|
| `JIRA_URL` | Your Jira instance URL |
| `JIRA_USER` | Your Jira account email |
| `JIRA_API_TOKEN` | Your Jira API token |

Example:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

## Local usage

From the workspace root:

```bash
uv sync --all-packages --group dev
uv run --package jira2cli jira2cli --help
uv run --package jira2cli jira2cli read PROJ-123
uv run --package jira2cli jira2cli search 'project = PROJ ORDER BY updated DESC'
uv run --package jira2cli jira2cli fields --project-key PROJ
```

## Workspace layout

- `packages/jira2ai-core` — shared operations.
- `packages/jira2mcp` — MCP adapter published as `jira2mcp`.
- `packages/jira2cli` — CLI adapter package.

For MCP installs and Claude setup, use `uvx jira2mcp` and `claude mcp add jira -- uvx jira2mcp` as documented in the repository root README.

## Maintainers

Do not assume `uvx jira2cli` or `pip install jira2cli` is available yet. Keep using local workspace commands until the release gates in the maintainer docs are completed.

Release sequencing, package tags, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2mcp/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2mcp/blob/main/CONTRIBUTING.md>
