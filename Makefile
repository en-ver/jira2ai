.PHONY: lint format type-check check clean help build release

help:
	@echo "Available targets:"
	@echo "  lint        - Run ruff linting with auto-fix"
	@echo "  format      - Run ruff formatting"
	@echo "  type-check  - Run ty type checking"
	@echo "  check       - Run all checks (lint, format, type-check)"
	@echo "  build       - Build sdist and wheel"
	@echo "  release     - Create a release (usage: make release v=0.2.0)"
	@echo "  clean       - Clean Python cache files"
	@echo "  help        - Show this help message"

# Run ruff linting with auto-fix
lint:
	uv run ruff check --fix src

# Run ruff formatting
format:
	uv run ruff format src

# Run ty type checking
type-check:
	uv run ty check src/

# Run all checks
check: lint format type-check

# Build sdist and wheel
build: clean
	uv build

# Create a release: make release v=0.2.0
release:
ifndef v
	$(error Usage: make release v=0.2.0)
endif
	@echo "Releasing v$(v)..."
	@# Update version in pyproject.toml
	perl -i -pe 's/^version = ".*"/version = "$(v)"/' pyproject.toml
	@# Run all checks before releasing
	$(MAKE) check
	@# Commit, tag, and push
	git add pyproject.toml
	git diff --cached --quiet && echo "Version already set to $(v), skipping commit." || git commit -m "release: v$(v)"
	git tag -f "v$(v)"
	git push origin main "v$(v)" --force
	@echo "Release v$(v) pushed. CI will build, create GitHub Release, and publish to PyPI."

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/ .ty/ .ruff_cache/ .pytest_cache/
