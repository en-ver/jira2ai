from __future__ import annotations

from pathlib import Path

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "publish.yml"
)


def read_workflow() -> str:
    return WORKFLOW_PATH.read_text()


def test_publish_workflow_uses_only_package_specific_tag_triggers() -> None:
    workflow = read_workflow()

    assert '- "v*"' not in workflow
    assert workflow.count('- "jira2') == 2
    assert '- "jira2mcp-v*"' in workflow
    assert '- "jira2cli-v*"' in workflow


def test_publish_workflow_uses_package_aware_validation() -> None:
    workflow = read_workflow()

    assert "scripts/bump_version.py --validate-tag" in workflow
    assert "--validate-release" in workflow
    assert "--require-published-core" not in workflow
    assert "needs.validate-tag.outputs.package" in workflow


def test_publish_workflow_checks_only_wrapper_paths() -> None:
    workflow = read_workflow()

    assert "packages/jira2mcp/src" in workflow
    assert "packages/jira2cli/src" in workflow


def test_publish_workflow_builds_only_the_tagged_package() -> None:
    workflow = read_workflow()

    assert workflow.count("uv build --package") == 1
    assert 'uv build --package "${PACKAGE}"' in workflow
    assert "build-all" not in workflow


def test_publish_workflow_uses_oidc_without_token_fallback() -> None:
    workflow = read_workflow()

    assert "id-token: write" in workflow
    assert "PYPI_API_TOKEN" not in workflow
    assert "password:" not in workflow
    assert "secrets.PYPI" not in workflow


def test_publish_workflow_uses_package_specific_pypi_environment_url() -> None:
    workflow = read_workflow()

    assert "https://pypi.org/p/${{ needs.validate-tag.outputs.package }}" in workflow
    assert "https://pypi.org/p/jira2mcp" not in workflow
