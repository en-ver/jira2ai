from __future__ import annotations

import tomllib
from inspect import signature
from pathlib import Path

from jira2cli import app
from jira2py import __version__ as jira2py_version
from jira2py.helpers.issues import IssueHelpers
from jira2py.helpers.metadata import MetadataHelpers
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_wrappers_pin_published_jira2py_without_bumping_wrapper_versions() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    jira2py = next(
        package
        for package in lock["package"]
        if package["name"] == "jira2py" and package["version"] == "0.12.0"
    )

    for package_name in ("jira2cli", "jira2mcp"):
        project = tomllib.loads(
            (ROOT / "packages" / package_name / "pyproject.toml").read_text()
        )["project"]
        assert project["version"] == "0.4.0"
        assert "jira2py==0.12.0" in project["dependencies"]

        locked_wrapper = next(
            package for package in lock["package"] if package["name"] == package_name
        )
        requires_dist = locked_wrapper["metadata"]["requires-dist"]
        assert {
            entry["specifier"] for entry in requires_dist if entry["name"] == "jira2py"
        } == {"==0.12.0"}

    assert jira2py["source"] == {"registry": "https://pypi.org/simple"}
    assert jira2py["sdist"]["url"].startswith("https://files.pythonhosted.org/")
    assert jira2py["wheels"][0]["url"].startswith("https://files.pythonhosted.org/")
    assert jira2py_version == "0.12.0"
    assert set(signature(MetadataHelpers.transitions).parameters) == {
        "self",
        "issue_key",
        "transition_id",
        "include_unavailable_transitions",
    }
    assert set(signature(IssueHelpers.transition).parameters) == {
        "self",
        "issue_key",
        "transition",
        "fields",
        "update",
    }


def test_transition_docs_and_skill_match_current_cli_help() -> None:
    discovery_help = runner.invoke(app, ["transitions", "--help"])
    mutation_help = runner.invoke(app, ["transition", "--help"])

    assert discovery_help.exit_code == 0
    assert "--transition-id" in discovery_help.stdout
    assert "--include-unavailable" in discovery_help.stdout
    assert mutation_help.exit_code == 0
    assert "--fields-json" in mutation_help.stdout
    assert "--update-json" in mutation_help.stdout

    cli_readme = (ROOT / "packages/jira2cli/README.md").read_text()
    mcp_readme = (ROOT / "packages/jira2mcp/README.md").read_text()
    skill = (ROOT / "skills/jira2cli/SKILL.md").read_text()
    transition_reference = (
        ROOT / "skills/jira2cli/references/transitions-and-filters.md"
    ).read_text()

    for text in (cli_readme, skill, transition_reference):
        assert "--transition-id" in text
        assert "--include-unavailable" in text
        assert "--fields-json" in text
        assert "--update-json" in text
        assert "204 No Content" in text
        assert "blindly retry" in text
    for text in (mcp_readme, transition_reference):
        assert "transition action ID" in text
        assert "status ID" in text
        assert "ADF" in text
        assert "not secret storage" in text
    assert "include_unavailable_transitions" in mcp_readme
    assert "fields" in mcp_readme
    assert "update" in mcp_readme
    assert (
        "Dedicated description parameters and comment-command bodies accept Markdown"
        in cli_readme
    )
    assert "Dedicated description and comment parameters accept Markdown" in mcp_readme

    transition_guidance = (cli_readme, mcp_readme, skill, transition_reference)
    for text in transition_guidance:
        assert "must already be Jira-native ADF" in text
        assert "permission to transition the issue" in text
    assert "transitions PROJ-123 --json" in cli_readme
    assert "transitions <KEY> --json" in skill
    assert "transitions <KEY> --json" in transition_reference
    assert "include-unavailable --json\nuvx jira2cli transition" not in cli_readme
