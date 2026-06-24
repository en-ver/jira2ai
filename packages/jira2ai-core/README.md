# jira2ai-core

Shared Jira operations and formatting utilities used by the `jira2mcp` MCP adapter and the `jira2cli` CLI adapter.

This package is part of the workspace in this repository. It is not the end-user MCP entry point; for MCP installs, keep using `uvx jira2mcp`.

## Local development

From the workspace root:

```bash
uv sync --all-packages --group dev
uv build --package jira2ai-core
```

## Maintainers

`jira2ai-core` has its own version and future tags use `jira2ai-core-vX.Y.Z`.

Release sequencing, stop gates, and Trusted Publishing boundaries:

- <https://github.com/en-ver/jira2ai/blob/main/docs/releasing.md>
- <https://github.com/en-ver/jira2ai/blob/main/CONTRIBUTING.md>
