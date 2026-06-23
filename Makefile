.PHONY: lint format type-check check check-ci clean help build bump-version version-current release-prep release push-release-tag ensure-main-clean

PART ?= patch
VERSION_INPUT := $(or $(VERSION),$(v))

help:
	@echo "Available targets:"
	@echo "  lint             - Run ruff linting with auto-fix"
	@echo "  format           - Run ruff formatting"
	@echo "  type-check       - Run ty type checking"
	@echo "  check            - Run mutating local checks (lint, format, type-check)"
	@echo "  check-ci         - Run non-mutating CI-style checks"
	@echo "  build            - Build sdist and wheel"
	@echo "  bump-version     - Bump version (default patch) or set VERSION=0.2.0 / v=0.2.0"
	@echo "  version-current  - Print the current project version"
	@echo "  release-prep     - Bump version and run non-mutating checks"
	@echo "  release          - Create a local annotated release tag from a clean main branch"
	@echo "  push-release-tag - Push the current release tag only"
	@echo "  clean            - Clean Python cache files"
	@echo "  help             - Show this help message"

# Run ruff linting with auto-fix
lint:
	uv run ruff check --fix src scripts

# Run ruff formatting
format:
	uv run ruff format src scripts

# Run ty type checking
type-check:
	uv run ty check src/ scripts/

# Run all checks
check: lint format type-check

# Run non-mutating CI-style checks
check-ci:
	uv run --locked ruff check src scripts
	uv run --locked ruff format --check src scripts
	uv run --locked ty check src/ scripts/

# Build sdist and wheel
build: clean
	uv build

# Print the current project version
version-current:
	@uv run --frozen python scripts/bump_version.py --current

# Bump the project version
bump-version:
	@args="--part $(PART)"; \
	if [ -n "$(VERSION_INPUT)" ]; then args="--version $(VERSION_INPUT)"; fi; \
	new_version="$$(uv run --frozen python scripts/bump_version.py $$args)" || exit $$?; \
	echo "Version set to $$new_version"

# Prepare a release before opening a PR to main
release-prep:
	$(MAKE) bump-version VERSION="$(VERSION_INPUT)" PART="$(PART)"
	uv lock
	$(MAKE) check-ci
	$(MAKE) build
	@echo "Release prep complete for v$$(uv run --locked python scripts/bump_version.py --current)"
	@echo "Review the diff and open a PR from dev to main."

# Require a clean main branch before tagging a release
ensure-main-clean:
	@test "$$(git branch --show-current)" = "main" || (echo "Release tagging must be run from the main branch." && exit 1)
	@git diff --quiet || (echo "Working tree must be clean before tagging a release." && exit 1)
	@git diff --cached --quiet || (echo "Index must be clean before tagging a release." && exit 1)

# Create a local release tag without pushing main or force-updating tags
release: ensure-main-clean
	@version="$$(uv run --frozen python scripts/bump_version.py --current)"; \
	if git rev-parse -q --verify "refs/tags/v$$version" >/dev/null; then \
		echo "Local tag v$$version already exists."; \
		exit 1; \
	fi; \
	if git ls-remote --exit-code --tags origin "refs/tags/v$$version" >/dev/null 2>&1; then \
		echo "Remote tag v$$version already exists."; \
		exit 1; \
	fi; \
	git tag -a "v$$version" -m "Release v$$version"; \
	echo "Created local tag v$$version"

# Push the release tag only to trigger publishing
push-release-tag:
	@version="$$(uv run --frozen python scripts/bump_version.py --current)"; \
	git rev-parse -q --verify "refs/tags/v$$version" >/dev/null || { echo "Local tag v$$version does not exist."; exit 1; }; \
	git push origin "refs/tags/v$$version"

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/ .ty/ .ruff_cache/ .pytest_cache/ dist/ build/ *.egg-info
