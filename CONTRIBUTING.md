# Contributing

Thanks for contributing to jira2mcp.

## Development checks

This repository uses a root `uv` workspace and the root `Makefile` for local development commands.

Current package layout:

- `packages/jira2ai-core` — shared Jira operations used by both adapters.
- `packages/jira2mcp` — FastMCP server/adapter package published as `jira2mcp`.
- `packages/jira2cli` — CLI adapter package for local/dev use.

Both adapters use the same Jira environment variables:

- `JIRA_URL`
- `JIRA_USER`
- `JIRA_API_TOKEN`

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
make build-all
uv run --package jira2cli jira2cli --help
```

`make test` runs the pytest suite.

`make check` runs the mutating local lint, format, and type-check targets.

`make check-ci` runs the non-mutating CI-style checks across all three package source trees, `scripts`, and the test suite.

`make build` keeps the existing `jira2mcp` package build used by the current release flow.

`make build-all` builds `jira2ai-core`, `jira2mcp`, and `jira2cli` for local verification.

## Release note

The existing `v*` publish workflow still validates the full workspace, but it only builds, releases, and publishes `jira2mcp`.

Do not cut a release for `jira2ai-core` or `jira2cli` yet, and do not change the current tag/publish flow in this stage.

To see the available development targets, run:

```bash
make help
```
