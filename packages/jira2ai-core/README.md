# jira2ai-core

Shared Jira operations and formatting utilities used by the `jira2mcp` MCP adapter and the `jira2cli` CLI adapter.

This package is part of the workspace in this repository. It is not the end-user MCP entry point; for MCP installs, keep using `uvx jira2mcp`.

## Local development

From the workspace root:

```bash
uv sync --all-packages --group dev
uv build --package jira2ai-core
```

## Shared operations

- `get_worklog_report(...)` powers `jira_worklog_report` and `jira2cli worklog-report`.
- Required inputs: `start_date`, `end_date`, and `jql`.
- Optional inputs: `account_id`, `max_issues` (default `100`, minimum `1`, with truncation noted when more issues match), and `include_details`.
- Issue selection is JQL-only. For a single issue, use JQL such as `issue = PROJ-123`.
- Dates are interpreted in UTC, and `end_date` is inclusive.
- `account_id` filtering is applied client-side by worklog author `accountId`.
- Output rows use `displayName` as the friendly user name.
- Results depend on the configured Jira account's issue/worklog visibility and permissions.

## Maintainers

`jira2ai-core` has its own version and future tags use `jira2ai-core-vX.Y.Z`.

Release sequencing, stop gates, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2ai/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md>
