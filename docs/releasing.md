# Releasing

This workspace has three independently versioned packages:

- `jira2ai-core`
- `jira2mcp`
- `jira2cli`

Future release tags must be package-specific:

- `jira2ai-core-vX.Y.Z`
- `jira2mcp-vX.Y.Z`
- `jira2cli-vX.Y.Z`

Legacy `v0.1.0` and `v0.1.1` tags are historical only. Do not use broad future `v*` tags.

## Current stop gates

Do not tag, push release tags, create GitHub Releases, or publish to PyPI in this migration until the following are verified manually:

- `.github/workflows/publish.yml` is the workflow that will handle package publishing.
- GitHub environment `pypi` exists for that workflow.
- Publishing uses OIDC / Trusted Publishing only.
- No PyPI API token fallback is configured or used.
- The current repository is still `en-ver/jira2mcp`.
- After the GitHub repo is renamed to `en-ver/jira2ai`, the PyPI Trusted Publisher repository setting must be updated for each package.
- `jira2ai-core` and `jira2cli` each need PyPI Trusted Publisher registration before their first publish.

These are boundaries to verify before release operations, not confirmation that setup is already complete.

## Release order

When an adapter needs a new core version:

1. Release `jira2ai-core` first.
2. Wait until that exact `jira2ai-core` version is visible on PyPI.
3. Release `jira2mcp` and/or `jira2cli` only after their exact `jira2ai-core==...` dependency is published.

`jira2mcp` and `jira2cli` intentionally use exact `jira2ai-core==...` dependencies. `release-prep` and the publish workflow will block adapter releases until the pinned core version is published.

## Local release helper commands

Check a package version:

```bash
make version-current PACKAGE=jira2ai-core
make version-current PACKAGE=jira2mcp
make version-current PACKAGE=jira2cli
```

Prepare a package release on a working branch:

```bash
make release-prep PACKAGE=jira2ai-core VERSION=0.1.0
make release-prep PACKAGE=jira2mcp VERSION=0.1.2
make release-prep PACKAGE=jira2cli VERSION=0.1.0
```

`make release-prep PACKAGE=... VERSION=...` currently:

1. validates the selected package,
2. requires published core availability for adapter packages,
3. bumps the selected package version,
4. runs `uv lock`,
5. runs `make check-ci`, and
6. builds only the selected package.

Create the local annotated release tag from a clean `main` branch:

```bash
make release PACKAGE=jira2ai-core
make release PACKAGE=jira2mcp
make release PACKAGE=jira2cli
```

Push only the current package tag to trigger publishing:

```bash
make push-release-tag PACKAGE=jira2ai-core
make push-release-tag PACKAGE=jira2mcp
make push-release-tag PACKAGE=jira2cli
```

Those commands create and push tags in the forms documented above, for example `jira2mcp-v0.1.2`.

## Trusted Publishing boundary

Repository files now assume this release shape:

- workflow file: `.github/workflows/publish.yml`
- GitHub environment: `pypi`
- PyPI auth model: OIDC / Trusted Publishing only
- PyPI auth fallback: none; do not add API tokens unless policy changes explicitly

Operational notes:

- The repo has not been renamed yet; it is still `en-ver/jira2mcp`.
- After renaming the repo to `en-ver/jira2ai`, update the Trusted Publisher repository setting for every package in PyPI.
- `jira2mcp` already has release history, but its publisher settings still need to match the final repo name after rename.
- `jira2ai-core` and `jira2cli` must be registered in PyPI Trusted Publishing before their first publish.

Until those checks are complete, stop before `make release`, `make push-release-tag`, or any manual publish step.
