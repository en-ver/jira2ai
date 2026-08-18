# Contributing

Thanks for contributing to the Jira AI workspace.

## Development checks

This repository uses a root `uv` workspace and the root `Makefile` for local development commands. The commands in this guide are repository-local contributor commands, not consumer installation commands.

Current package layout:

- `packages/jira2mcp` — FastMCP server/adapter package published as `jira2mcp`.
- `packages/jira2cli` — published CLI adapter package.

Both packages use the same Jira environment variables:

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
uv run --locked jira2cli --help
```

## `jira2cli` skill/CLI alignment rule

Any future change to `skills/jira2cli`, `packages/jira2cli/src/jira2cli/cli.py`, `packages/jira2cli/src/jira2cli/commands/*.py`, or `packages/jira2cli/README.md` must verify that the skill docs still match the current CLI.

Required alignment check:

- compare the skill text against `packages/jira2cli/src/jira2cli/cli.py`
- compare the skill text against `packages/jira2cli/src/jira2cli/commands/*.py`
- compare the skill text against `packages/jira2cli/README.md`
- verify the documented command surface and options against current help output from `uv run --locked jira2cli --help` and each command `--help`

Do not merge `jira2cli` skill or CLI docs/implementation changes without this verification.

`make test` runs the pytest suite.

`make check` runs the mutating local lint, format, and type-check targets.

`make check-ci` runs the non-mutating CI-style checks across both package source trees, `scripts`, and the test suite.

`make build` keeps the existing `jira2mcp` default package build used by the current release flow.

`make build-all` builds `jira2mcp` and `jira2cli` for local verification.

## Release process

Maintainers should use the package-aware release notes in [docs/releasing.md](docs/releasing.md).

Future releases use package-specific tags only:

- `jira2mcp-vX.Y.Z`
- `jira2cli-vX.Y.Z`

Do not use broad future `v*` tags.

Current helper entry points:

```bash
make release-prep PACKAGE=jira2mcp VERSION=X.Y.Z
make release-prep PACKAGE=jira2cli VERSION=X.Y.Z
make release PACKAGE=jira2mcp
make push-release-tag PACKAGE=jira2mcp
```

Before any tag push, GitHub release, or PyPI publish, follow the Trusted Publishing and repository-boundary checks in `docs/releasing.md`.

To see the available development targets, run:

```bash
make help
```
