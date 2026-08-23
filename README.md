# jira2ai

Jira Cloud integrations for AI clients and local automation. Requires Python 3.13+.

## Choose a product

- **[jira2mcp](packages/jira2mcp/README.md)** — the published MCP server. Use it with any MCP client that supports a stdio server; Claude Code is one example.
- **[jira2cli](packages/jira2cli/README.md)** — the published flat Jira Cloud CLI. Run it with `uvx jira2cli`; local checkout commands are for contributors.

Both are **Jira Cloud only**. They do not support Jira Server or Data Center, and do not provide dedicated issue assignment, issue delete/archive, sprint/board/epic, or admin-configuration operations.

## Start with MCP

Install [uv](https://docs.astral.sh/uv/) and configure your MCP client to launch the published server over stdio:

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

For Claude Code, the equivalent command is:

```bash
claude mcp add jira -- uvx jira2mcp
```

See the [MCP guide](packages/jira2mcp/README.md) for client configuration, the complete `jira_*` tool inventory, and examples.

## Use the CLI

Install [uv](https://docs.astral.sh/uv/) on Python 3.13 or later, configure credentials below, then run the published CLI:

```bash
uvx jira2cli --help
uvx jira2cli auth-status
uvx jira2cli read PROJ-123 --fields summary,status --json
```

## Authentication and safety

Set these environment variables for either product:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"
```

Create an API token in your [Atlassian account](https://id.atlassian.com/manage-profile/security/api-tokens). Both products also accept an explicit JSON credentials file through `--credentials-file`; that explicit file is used instead of environment credentials. There is no default credentials-file path and no `JIRA_CREDENTIALS_FILE` environment variable.

Keep API tokens out of source control, logs, prompts, and shared client configuration. Jira access is limited by the configured account's Jira permissions. Read metadata and the current issue state before writes, then confirm the exact fields, IDs, transition, or destructive action.

## What you can do

The products support authentication checks, issue reads and JQL search, projects and field metadata, comments, transitions, saved filters, issue links, attachments, and worklogs. Descriptions and comments accept Markdown. Plain CLI issue reads can render selected rich-text fields, while JSON and MCP structured issue reads preserve Jira's raw field data.

For local development or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md). Contributors working from a repository checkout use `uv run --locked jira2cli ...` after workspace setup. The optional [Pi CLI skill](skills/jira2cli/SKILL.md) is a source-checkout template for agents using `jira2cli`; UVX runs the CLI but does not install or auto-discover the skill.

## License

MIT
