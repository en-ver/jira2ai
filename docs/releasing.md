# Releasing

This workspace has two independently versioned packages:

- `jira2mcp`
- `jira2cli`

Future release tags must be package-specific:

- `jira2mcp-vX.Y.Z`
- `jira2cli-vX.Y.Z`

Legacy broad `v*` tags are historical only. Do not use them for future releases.

## Release boundaries

Prepare each release on a feature branch and merge its pull request into `main` before tagging. Before tag, GitHub Release, or PyPI publish operations, verify:

- package publishing uses `.github/workflows/publish.yml` and GitHub environment `pypi`;
- the PyPI Trusted Publisher maps owner `en-ver`, repository `jira2ai`, workflow `.github/workflows/publish.yml`, and environment `pypi`;
- publishing uses OIDC / Trusted Publishing only, with no PyPI API-token fallback; and
- the release tag is created from clean, current `main`.

These are per-release operational checks; do not proceed if any mapping or boundary differs.

## Release readiness

`jira2mcp` and `jira2cli` are thin wrappers over published `jira2py` helpers. There is no longer a workspace-internal core package release order.

## Local release helper commands

Check a package version:

```bash
make version-current PACKAGE=jira2mcp
make version-current PACKAGE=jira2cli
```

Prepare a package release on its feature branch:

```bash
make release-prep PACKAGE=jira2mcp VERSION=X.Y.Z
make release-prep PACKAGE=jira2cli VERSION=X.Y.Z
```

`make release-prep PACKAGE=... VERSION=...` currently:

1. validates the selected package,
2. bumps the selected package project version,
3. runs `uv lock`,
4. runs `make check-ci`, and
5. builds only the selected package.

For a `jira2cli` release, explicitly synchronize `packages/jira2cli/src/jira2cli/__init__.py` `__version__` with the selected release version: the helper does not update it. Then run `uv lock`, `make check-ci`, and `make build PACKAGE=jira2cli`, and confirm the source and package versions agree before opening the release-prep PR.

After that PR is merged, create the local annotated release tag from clean `main`:

```bash
make release PACKAGE=jira2mcp
make release PACKAGE=jira2cli
```

Push only the current package tag to trigger publishing:

```bash
make push-release-tag PACKAGE=jira2mcp
make push-release-tag PACKAGE=jira2cli
```

Those commands create and push tags in the forms documented above, such as `jira2mcp-vX.Y.Z`.

## Trusted Publishing boundary

The release workflow is `.github/workflows/publish.yml`, uses GitHub environment `pypi`, and must publish through OIDC / Trusted Publishing only. For each release, verify the Trusted Publisher mapping is owner `en-ver`, repository `jira2ai`, workflow `.github/workflows/publish.yml`, and environment `pypi`; do not add or use a PyPI API-token fallback unless policy changes explicitly.

Stop before `make release`, `make push-release-tag`, or any manual publish step if those checks fail.
