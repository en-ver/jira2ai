# Releasing

This workspace has two independently versioned packages:

- `jira2mcp`
- `jira2cli`

Future release tags must be package-specific:

- `jira2mcp-vX.Y.Z`
- `jira2cli-vX.Y.Z`

Legacy `v0.1.0` and `v0.1.1` tags are historical only. Do not use broad future `v*` tags.

## Current stop gates

Do not tag, push release tags, create GitHub Releases, or publish to PyPI in this migration until the following are verified manually:

- `.github/workflows/publish.yml` is the workflow that will handle package publishing.
- GitHub environment `pypi` exists for that workflow.
- Publishing uses OIDC / Trusted Publishing only.
- No PyPI API token fallback is configured or used.
- The repository is now `en-ver/jira2ai`.
- Before the first post-rename release, verify PyPI Trusted Publishers are configured for owner `en-ver`, repository `jira2ai`, workflow `.github/workflows/publish.yml`, and environment `pypi`.
- The existing `jira2mcp` PyPI project publisher must be updated to repository `jira2ai` before the first post-rename release.
- `jira2cli` must be registered in PyPI Trusted Publishing for repository `jira2ai` before its first publish.

These are boundaries to verify before release operations, not confirmation that setup is already complete.

## Release readiness

`jira2mcp` and `jira2cli` are thin wrappers over published `jira2py` helpers. There is no longer a workspace-internal core package release order.

## Local release helper commands

Check a package version:

```bash
make version-current PACKAGE=jira2mcp
make version-current PACKAGE=jira2cli
```

Prepare a package release on a working branch:

```bash
make release-prep PACKAGE=jira2mcp VERSION=0.1.2
make release-prep PACKAGE=jira2cli VERSION=0.1.0
```

`make release-prep PACKAGE=... VERSION=...` currently:

1. validates the selected package,
2. bumps the selected package version,
3. runs `uv lock`,
4. runs `make check-ci`, and
5. builds only the selected package.

Create the local annotated release tag from a clean `main` branch:

```bash
make release PACKAGE=jira2mcp
make release PACKAGE=jira2cli
```

Push only the current package tag to trigger publishing:

```bash
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

- The repository is now `en-ver/jira2ai`.
- Before the first post-rename release, verify each PyPI Trusted Publisher is configured for owner `en-ver`, repository `jira2ai`, workflow `.github/workflows/publish.yml`, and environment `pypi`.
- `jira2mcp` already has release history, but its existing PyPI Trusted Publisher settings must be updated to repository `jira2ai` before the first post-rename release.
- `jira2cli` must be registered in PyPI Trusted Publishing for repository `jira2ai` before its first publish.

Until those checks are complete, stop before `make release`, `make push-release-tag`, or any manual publish step.
