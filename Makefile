.PHONY: lint format type-check test check check-ci clean help build build-jira2ai-core build-jira2mcp build-jira2cli build-all bump-version version-current release-prep release push-release-tag ensure-main-clean

PACKAGE ?= jira2mcp
PART ?= patch
VERSION_INPUT := $(or $(VERSION),$(v))
MCP_PACKAGE_DIR := packages/jira2mcp
CORE_PACKAGE_DIR := packages/jira2ai-core
CLI_PACKAGE_DIR := packages/jira2cli
CHECK_PATHS := $(CORE_PACKAGE_DIR)/src $(MCP_PACKAGE_DIR)/src $(CLI_PACKAGE_DIR)/src scripts tests
TYPECHECK_PATHS := $(CORE_PACKAGE_DIR)/src/ $(MCP_PACKAGE_DIR)/src/ $(CLI_PACKAGE_DIR)/src/ scripts/

help:
	@echo "Available targets:"
	@echo "  lint             - Run ruff linting with auto-fix"
	@echo "  format           - Run ruff formatting"
	@echo "  type-check       - Run ty type checking"
	@echo "  test             - Run pytest"
	@echo "  check            - Run mutating local checks (lint, format, type-check)"
	@echo "  check-ci         - Run non-mutating CI-style checks, including tests"
	@echo "  build            - Build the selected package (default: jira2mcp; override with PACKAGE=...)"
	@echo "  build-jira2ai-core - Build jira2ai-core sdist and wheel"
	@echo "  build-jira2mcp   - Build jira2mcp sdist and wheel"
	@echo "  build-jira2cli   - Build jira2cli sdist and wheel"
	@echo "  build-all        - Build all workspace packages"
	@echo "  bump-version     - Bump selected package version (default patch) or set VERSION=0.2.0 / v=0.2.0"
	@echo "  version-current  - Print the current selected package version"
	@echo "  release-prep     - Validate selected package release readiness, bump version, and run non-mutating checks"
	@echo "  release          - Create a local annotated release tag for the selected package from a clean main branch"
	@echo "  push-release-tag - Push the current selected package release tag only"
	@echo "  clean            - Clean Python cache files"
	@echo "  help             - Show this help message"

# Run ruff linting with auto-fix
lint:
	uv run ruff check --fix $(CHECK_PATHS)

# Run ruff formatting
format:
	uv run ruff format $(CHECK_PATHS)

# Run ty type checking
type-check:
	uv run ty check $(TYPECHECK_PATHS)

# Run pytest
test:
	uv run pytest

# Run all checks
check: lint format type-check

# Run non-mutating CI-style checks
check-ci:
	uv run --locked ruff check $(CHECK_PATHS)
	uv run --locked ruff format --check $(CHECK_PATHS)
	uv run --locked ty check $(TYPECHECK_PATHS)
	uv run --locked pytest

# Build sdist and wheel
build: clean
	uv build --package $(PACKAGE)

build-jira2ai-core:
	uv build --package jira2ai-core

build-jira2mcp:
	uv build --package jira2mcp

build-jira2cli:
	uv build --package jira2cli

build-all: clean build-jira2ai-core build-jira2mcp build-jira2cli

# Print the current project version
version-current:
	@uv run --frozen python scripts/bump_version.py --package "$(PACKAGE)" --current

# Bump the project version
bump-version:
	@args="--part $(PART)"; \
	if [ -n "$(VERSION_INPUT)" ]; then args="--version $(VERSION_INPUT)"; fi; \
	new_version="$$(uv run --frozen python scripts/bump_version.py --package "$(PACKAGE)" $$args)" || exit $$?; \
	echo "Version set to $$new_version"

# Prepare a release before opening a PR to main
release-prep:
	@uv run --frozen python scripts/bump_version.py --package "$(PACKAGE)" --validate-release --require-published-core
	$(MAKE) bump-version PACKAGE="$(PACKAGE)" VERSION="$(VERSION_INPUT)" PART="$(PART)"
	uv lock
	$(MAKE) check-ci
	$(MAKE) build PACKAGE="$(PACKAGE)"
	@echo "Release prep complete for $(PACKAGE)-v$$(uv run --locked python scripts/bump_version.py --package "$(PACKAGE)" --current)"
	@echo "Review the diff and open a PR from dev to main."

# Require a clean main branch before tagging a release
ensure-main-clean:
	@test "$$(git branch --show-current)" = "main" || (echo "Release tagging must be run from the main branch." && exit 1)
	@git diff --quiet || (echo "Working tree must be clean before tagging a release." && exit 1)
	@git diff --cached --quiet || (echo "Index must be clean before tagging a release." && exit 1)

# Create a local release tag without pushing main or force-updating tags
release: ensure-main-clean
	@version="$$(uv run --frozen python scripts/bump_version.py --package "$(PACKAGE)" --current)"; \
	tag="$(PACKAGE)-v$$version"; \
	if git rev-parse -q --verify "refs/tags/$$tag" >/dev/null; then \
		echo "Local tag $$tag already exists."; \
		exit 1; \
	fi; \
	if git ls-remote --exit-code --tags origin "refs/tags/$$tag" >/dev/null 2>&1; then \
		echo "Remote tag $$tag already exists."; \
		exit 1; \
	fi; \
	git tag -a "$$tag" -m "Release $$tag"; \
	echo "Created local tag $$tag"

# Push the release tag only to trigger publishing
push-release-tag:
	@version="$$(uv run --frozen python scripts/bump_version.py --package "$(PACKAGE)" --current)"; \
	tag="$(PACKAGE)-v$$version"; \
	git rev-parse -q --verify "refs/tags/$$tag" >/dev/null || { echo "Local tag $$tag does not exist."; exit 1; }; \
	git push origin "refs/tags/$$tag"

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	rm -rf .mypy_cache/ .ty/ .ruff_cache/ .pytest_cache/ dist/ build/ $(CORE_PACKAGE_DIR)/dist/ $(CORE_PACKAGE_DIR)/build/ $(MCP_PACKAGE_DIR)/dist/ $(MCP_PACKAGE_DIR)/build/ $(CLI_PACKAGE_DIR)/dist/ $(CLI_PACKAGE_DIR)/build/
