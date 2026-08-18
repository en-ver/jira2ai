# jira2cli

A flat CLI for **Jira Cloud**. Requires Python >=3.13.

`jira2cli` is published on PyPI. Install [uv](https://docs.astral.sh/uv/) and run it with `uvx jira2cli`; for repository checkout and contributor setup, see the [contributing guide](https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md).

It does not support Jira Server or Data Center, and does not provide dedicated issue assignment, issue delete/archive, sprint/board/epic, or admin-configuration operations.

## Authentication and usage

Authenticate with either an explicit credentials file or environment variables:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USER="you@company.com"
export JIRA_API_TOKEN="your-api-token"

uvx jira2cli auth-status
uvx jira2cli read PROJ-123 --json
```

An explicit credentials file takes precedence over the environment:

```bash
uvx jira2cli --credentials-file ~/.config/jira-cloud.json me --json
```

```json
{
  "url": "https://yourcompany.atlassian.net",
  "username": "you@company.com",
  "api_token": "your-api-token"
}
```

There is no default credentials-file path and no `JIRA_CREDENTIALS_FILE` environment variable. Create a token in your [Atlassian account](https://id.atlassian.com/manage-profile/security/api-tokens); do not commit, print, or share it.

## Commands

Run `uvx jira2cli --help` for the current command and option help.

### Identity

`auth-status`, `me`

### Reads, search, and transitions

`read`, `comments`, `search`, `transitions`, `transition`

### Metadata and saved filters

`fields`, `project`, `projects`, `statuses`, `priorities`, `users`, `link-types`, `jql-syntax`, `filters`, `filter-run`

### Issues, comments, and links

`create`, `edit`, `comment`, `comment-update`, `comment-delete`, `issue-links`, `add-link`, `delete-link`

### Attachments and worklogs

`attachment`, `attachment-list`, `attachment-read`, `attachment-download`, `attachment-upload`, `attachment-delete`, `worklogs`, `worklog-add`, `worklog-update`, `worklog-delete`, `worklog-report`

Most structured commands accept `--json` for helper output or `--raw` for the untouched API payload; do not combine them. `filter-run` resolves a saved filter's JQL and returns the same search-shaped result as `search`.

## Examples

```bash
# Discover accessible projects and create/edit fields before a write.
uvx jira2cli projects --json
uvx jira2cli fields --project-key PROJ --issue-type Task --json

# Read and search.
uvx jira2cli read PROJ-123 --extra-field labels --json
uvx jira2cli search 'project = PROJ ORDER BY created DESC' --field key --field summary --json

# Inspect workflow choices before applying one.
uvx jira2cli transitions PROJ-123 --json
uvx jira2cli transition PROJ-123 "Start Progress" --json

# Reuse a saved filter.
uvx jira2cli filters --query mine --json
uvx jira2cli filter-run 10400 --field key --field summary --json

# Inspect attachments and worklogs.
uvx jira2cli attachment-list PROJ-123 --json
uvx jira2cli worklogs PROJ-123 --json
uvx jira2cli worklog-report --start-date 2026-06-12 --end-date 2026-06-13 --jql 'issue = PROJ-123' --json
```

Worklog-report dates are UTC and the end date is inclusive. It selects issues only with `--jql`; `--max-issues` defaults to 100 and limits the scanned issues. Results depend on the configured account's issue and worklog visibility.

## Local checkout contributors

From the repository root after workspace setup, contributors can run the checked-out CLI with:

```bash
uv run --locked jira2cli --help
```

## Safety and capabilities

Descriptions and comments accept Markdown and rich-text Jira fields are returned as Markdown. Use `fields` before create or edit; `users` before choosing a user; `transitions` before changing status; and `link-types` before creating links. Read the current issue before an update or destructive action, use exact IDs, and confirm the intended fields, transition, comment, attachment, link, or worklog before mutating Jira. Jira permissions control what the configured account can read or write.

The optional [Pi skill](https://github.com/en-ver/jira2ai/tree/main/skills/jira2cli) is a source-checkout template for agent workflows. Load it explicitly as `<path-to-jira2ai>/skills/jira2cli`; UVX runs the CLI but does not install or auto-discover the skill.

## License

MIT
