from __future__ import annotations

import tomllib
from inspect import signature
from pathlib import Path
from typing import Any, cast

from jira2cli import app
from jira2py import __version__ as jira2py_version
from jira2py.helpers.issues import IssueHelpers
from jira2py.helpers.metadata import MetadataHelpers
from typer.main import get_command

ROOT = Path(__file__).resolve().parents[1]


def test_wrappers_pin_published_jira2py_without_bumping_wrapper_versions() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    jira2py = next(
        package
        for package in lock["package"]
        if package["name"] == "jira2py" and package["version"] == "0.15.0"
    )

    for package_name in ("jira2cli", "jira2mcp"):
        project = tomllib.loads(
            (ROOT / "packages" / package_name / "pyproject.toml").read_text()
        )["project"]
        assert project["version"] == "0.7.0"
        assert "jira2py==0.15.0" in project["dependencies"]

        locked_wrapper = next(
            package for package in lock["package"] if package["name"] == package_name
        )
        assert locked_wrapper["version"] == "0.7.0"
        requires_dist = locked_wrapper["metadata"]["requires-dist"]
        assert {
            entry["specifier"] for entry in requires_dist if entry["name"] == "jira2py"
        } == {"==0.15.0"}

    assert jira2py["source"] == {"registry": "https://pypi.org/simple"}
    assert jira2py["sdist"]["url"].startswith("https://files.pythonhosted.org/")
    assert jira2py["wheels"][0]["url"].startswith("https://files.pythonhosted.org/")
    assert jira2py_version == "0.15.0"

    mcp_project = tomllib.loads(
        (ROOT / "packages" / "jira2mcp" / "pyproject.toml").read_text()
    )["project"]
    assert "adf-bridge>=0.1.3,<0.2" in mcp_project["dependencies"]
    assert not {
        "marklassian>=0.1.0",
        "pyadf>=0.3.0",
    } & set(mcp_project["dependencies"])

    adf_bridge = next(
        package
        for package in lock["package"]
        if package["name"] == "adf-bridge" and package["version"] == "0.1.3"
    )
    assert adf_bridge["source"] == {"registry": "https://pypi.org/simple"}
    assert adf_bridge["sdist"]["url"].startswith("https://files.pythonhosted.org/")
    assert adf_bridge["wheels"][0]["url"].startswith("https://files.pythonhosted.org/")
    assert {package["name"] for package in lock["package"]}.isdisjoint(
        {"marklassian", "pyadf"}
    )

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
    commands = cast(Any, get_command(app)).commands
    expected_visible_options = {
        "transitions": {
            "--transition-id",
            "--include-unavailable",
            "--raw",
            "--json",
        },
        "transition": {
            "--fields-json",
            "--update-json",
            "--raw",
            "--json",
        },
    }
    for command_name, expected_options in expected_visible_options.items():
        assert {
            option
            for parameter in commands[command_name].params
            if not parameter.hidden
            for option in parameter.opts
            if option.startswith("--")
        } == expected_options

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
    assert "High-level Markdown writes" in mcp_readme
    assert "[~accountId:<id>]" in mcp_readme

    transition_guidance = (cli_readme, mcp_readme, skill, transition_reference)
    for text in transition_guidance:
        assert "must already be Jira-native ADF" in text
        assert "permission to transition the issue" in text
    assert "transitions PROJ-123 --json" in cli_readme
    assert "transitions <KEY> --json" in skill
    assert "transitions <KEY> --json" in transition_reference
    assert (
        "Use `--include-unavailable` only to diagnose why an action is unavailable; "
        "never submit an unavailable action."
    ) in cli_readme


def test_markdown_attachment_image_docs_describe_current_surface() -> None:
    documents = {
        "root README": (ROOT / "README.md").read_text(),
        "CLI README": (ROOT / "packages" / "jira2cli" / "README.md").read_text(),
        "MCP README": (ROOT / "packages" / "jira2mcp" / "README.md").read_text(),
        "skill": (ROOT / "skills" / "jira2cli" / "SKILL.md").read_text(),
        "attachment reference": (
            ROOT / "skills" / "jira2cli" / "references" / "attachment-download.md"
        ).read_text(),
        "create reference": (
            ROOT / "skills" / "jira2cli" / "references" / "create-issue.md"
        ).read_text(),
        "edit reference": (
            ROOT / "skills" / "jira2cli" / "references" / "edit-issue.md"
        ).read_text(),
        "comment reference": (
            ROOT / "skills" / "jira2cli" / "references" / "comment-on-issue.md"
        ).read_text(),
        "worklog reference": (
            ROOT / "skills" / "jira2cli" / "references" / "worklog-management.md"
        ).read_text(),
    }
    assert all("![alt](attachment-content-url)" in text for text in documents.values())
    assert "content" in documents["attachment reference"]
    assert "explicit description option" in documents["root README"]
    assert "create the issue" in documents["create reference"].lower()
    assert "complete" in documents["edit reference"].lower()
    assert "structuredContent.data[0].content" in documents["MCP README"]
    for name in ("root README", "CLI README", "MCP README", "skill"):
        assert "sized transparently during ordinary Markdown writes" in documents[name]
        assert "document root and in Markdown lists" in documents[name]
        assert "External URLs are never fetched" in documents[name]
        assert "fails before Jira receives a mutation" in documents[name]
