from __future__ import annotations

import importlib.util
from pathlib import Path
from textwrap import dedent

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bump_version.py"
SPEC = importlib.util.spec_from_file_location("bump_version", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
bump_version = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bump_version)


@pytest.mark.parametrize("package", ["jira2ai-core", "jira2mcp", "jira2cli"])
def test_current_reads_selected_package_version(
    package: str, capsys: pytest.CaptureFixture[str]
) -> None:
    expected = bump_version.read_package_version(package)

    assert bump_version.main(["--package", package, "--current"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == expected
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package", "argv", "expected_version"),
    [
        ("jira2mcp", ["--package", "jira2mcp", "--version", "1.2.3"], "1.2.3"),
        ("jira2cli", ["--package", "jira2cli", "--part", "minor"], "0.2.0"),
    ],
)
def test_version_updates_only_selected_package(
    package: str,
    argv: list[str],
    expected_version: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    temp_paths: dict[str, Path] = {}
    original_versions: dict[str, str] = {}

    for supported_package, source_path in bump_version.PACKAGE_PYPROJECT_PATHS.items():
        target_path = tmp_path / supported_package / "pyproject.toml"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_path.read_text())
        temp_paths[supported_package] = target_path
        original_versions[supported_package] = bump_version.read_current_version(
            target_path
        )

    monkeypatch.setattr(bump_version, "PACKAGE_PYPROJECT_PATHS", temp_paths)

    assert bump_version.main(argv) == 0
    assert bump_version.read_current_version(temp_paths[package]) == expected_version

    for other_package, target_path in temp_paths.items():
        if other_package == package:
            continue
        assert (
            bump_version.read_current_version(target_path)
            == original_versions[other_package]
        )


@pytest.mark.parametrize(
    ("package", "pass_explicit_package"),
    [("jira2mcp", False), ("jira2ai-core", True)],
)
def test_validate_tag_accepts_package_specific_tags(
    package: str,
    pass_explicit_package: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tag = f"{package}-v{bump_version.read_package_version(package)}"
    argv = ["--validate-tag", tag]
    if pass_explicit_package:
        argv = ["--package", package, *argv]

    assert bump_version.main(argv) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == tag
    assert captured.err == ""


@pytest.mark.parametrize(
    ("tag", "message"),
    [
        ("v0.1.1", "Legacy tags like v0.1.1 are not supported"),
        ("unknown-v0.1.0", "Unsupported package: unknown"),
        (
            "jira2cli-v9.9.9",
            "Tag version 9.9.9 does not match jira2cli pyproject version",
        ),
    ],
)
def test_validate_tag_rejects_invalid_tags(
    tag: str,
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert bump_version.main(["--validate-tag", tag]) == 1

    captured = capsys.readouterr()
    assert message in captured.err
    assert captured.out == ""


def test_validate_tag_rejects_package_mismatch(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        bump_version.main(
            ["--package", "jira2cli", "--validate-tag", "jira2mcp-v0.1.1"]
        )
        == 1
    )

    captured = capsys.readouterr()
    assert "Package mismatch" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("package", ["jira2mcp", "jira2cli"])
def test_validate_release_accepts_exact_core_dependency(
    package: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    core_version = bump_version.read_exact_core_dependency_version(
        bump_version.get_package_pyproject_path(package)
    )

    assert bump_version.main(["--package", package, "--validate-release"]) == 0

    captured = capsys.readouterr()
    assert f"exact jira2ai-core=={core_version}" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    "dependencies",
    [["jira2ai-core>=0.1.0"], ["typer>=0.16.0"]],
)
def test_validate_release_rejects_missing_or_non_exact_core_dependency(
    dependencies: list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    temp_path = tmp_path / "jira2mcp" / "pyproject.toml"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(
        make_pyproject(
            name="jira2mcp",
            version="0.1.1",
            dependencies=dependencies,
        )
    )

    monkeypatch.setattr(
        bump_version,
        "PACKAGE_PYPROJECT_PATHS",
        {**bump_version.PACKAGE_PYPROJECT_PATHS, "jira2mcp": temp_path},
    )

    with pytest.raises(ValueError, match="jira2ai-core==X.Y.Z"):
        bump_version.validate_release_requirements("jira2mcp")


def test_validate_release_requires_published_core_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    core_version = bump_version.read_exact_core_dependency_version(
        bump_version.get_package_pyproject_path("jira2mcp")
    )
    monkeypatch.setattr(
        bump_version,
        "is_pypi_version_published",
        lambda package, version: package == "jira2ai-core" and version == core_version,
    )

    assert (
        bump_version.validate_release_requirements(
            "jira2mcp", require_published_core=True
        )
        == core_version
    )


def test_validate_release_rejects_unpublished_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bump_version,
        "is_pypi_version_published",
        lambda package, version: False,
    )

    with pytest.raises(RuntimeError, match="is not available on PyPI"):
        bump_version.validate_release_requirements(
            "jira2mcp", require_published_core=True
        )


def test_validate_release_skips_published_core_check_for_core_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(package: str, version: str) -> bool:
        raise AssertionError(f"Unexpected PyPI lookup for {package} {version}")

    monkeypatch.setattr(bump_version, "is_pypi_version_published", fail_if_called)

    assert (
        bump_version.validate_release_requirements(
            "jira2ai-core", require_published_core=True
        )
        is None
    )


def make_pyproject(*, name: str, version: str, dependencies: list[str]) -> str:
    dependency_lines = "\n".join(f'    "{dependency}",' for dependency in dependencies)
    return (
        dedent(
            f"""
        [project]
        name = "{name}"
        version = "{version}"
        dependencies = [
        {dependency_lines}
        ]
        """
        ).strip()
        + "\n"
    )
