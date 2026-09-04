from __future__ import annotations

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_PACKAGE = ROOT / "packages" / "jira2mcp"
MCP_SOURCE = MCP_PACKAGE / "src" / "jira2mcp"
WORKFLOW = ROOT / ".github" / "workflows" / "fastmcp-compat.yml"


def _tool_result_import_modules() -> list[str | None]:
    paths = [*MCP_SOURCE.rglob("*.py"), *(ROOT / "tests").rglob("*.py")]
    imports: list[str | None] = []
    for path in paths:
        tree = ast.parse(path.read_text(), filename=path)
        imports.extend(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(alias.name == "ToolResult" for alias in node.names)
        )
    return imports


def test_jira2mcp_fastmcp_dependency_is_bounded_and_registry_locked() -> None:
    project = tomllib.loads((MCP_PACKAGE / "pyproject.toml").read_text())["project"]
    assert "fastmcp>=3.2.0,<4" in project["dependencies"]

    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    jira2mcp = next(
        package for package in lock["package"] if package["name"] == "jira2mcp"
    )
    fastmcp = next(
        package for package in lock["package"] if package["name"] == "fastmcp"
    )
    fastmcp_slim = next(
        package for package in lock["package"] if package["name"] == "fastmcp-slim"
    )

    requires_dist = jira2mcp["metadata"]["requires-dist"]
    assert {
        entry["specifier"] for entry in requires_dist if entry["name"] == "fastmcp"
    } == {">=3.2.0,<4"}
    for package in (fastmcp, fastmcp_slim):
        assert package["version"] == "3.4.7"
        assert package["source"] == {"registry": "https://pypi.org/simple"}
        assert package["sdist"]["url"].startswith("https://files.pythonhosted.org/")
        assert package["wheels"][0]["url"].startswith("https://files.pythonhosted.org/")


def test_tool_result_imports_use_the_supported_public_module() -> None:
    import_modules = _tool_result_import_modules()

    assert import_modules
    assert set(import_modules) == {"fastmcp.tools"}


def test_fastmcp_compatibility_workflow_enforces_contract_and_smokes_endpoints() -> (
    None
):
    workflow = WORKFLOW.read_text()

    assert "pull_request:" in workflow
    assert "python -m pytest tests/test_fastmcp_compatibility.py" in workflow
    assert "needs: jira2mcp-fastmcp-contract" in workflow
    assert "uv build --package jira2mcp" in workflow
    assert 'requirement: "fastmcp==3.2.0"' in workflow
    assert 'requirement: "fastmcp>=3.2.0,<4"' in workflow
    assert "uv pip install --no-cache" in workflow
    assert '"$SMOKE_DIR/venv/bin/jira2mcp" --help' in workflow
    assert "scripts/smoke_jira2mcp_wheel.py" in workflow
    assert '--server "$SMOKE_DIR/venv/bin/jira2mcp"' in workflow
