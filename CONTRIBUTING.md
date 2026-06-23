# Contributing

Thanks for contributing to jira2mcp.

## Development checks

This repository uses a root `uv` workspace and the root `Makefile` for local development commands. The current package lives under `packages/jira2mcp`.

Set up the workspace with:

```bash
uv sync --all-packages --group dev
```

Before opening a pull request, run:

```bash
make check
make check-ci
make build
```

`make check` runs the mutating local lint, format, and type-check targets. `make check-ci` runs the non-mutating CI-style checks.

To see the available development targets, run:

```bash
make help
```
