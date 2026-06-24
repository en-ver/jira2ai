# Contributing

Thanks for contributing to jira2mcp.

## Development checks

This repository uses a root `uv` workspace and the root `Makefile` for local development commands.

Current package layout:

- `packages/jira2ai-core` — shared operation layer used internally by the MCP package.
- `packages/jira2mcp` — FastMCP server/adapter package published as `jira2mcp`.

Set up the workspace with:

```bash
uv sync --all-packages --group dev
```

Before opening a pull request, run:

```bash
make test
make check
make check-ci
make build
```

`make test` runs the pytest suite.

`make check` runs the mutating local lint, format, and type-check targets.

`make check-ci` runs the non-mutating CI-style checks across both package source trees, `scripts`, and the test suite.

## Release note

PR2 keeps the existing `jira2mcp`-only `v*` publish flow. Do not cut a release from this workspace-split state until `jira2ai-core` has a publish/install plan, or `jira2mcp` would depend on an unpublished package.

To see the available development targets, run:

```bash
make help
```
