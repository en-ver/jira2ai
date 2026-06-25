from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = "jira2mcp"
PACKAGE_PYPROJECT_PATHS = {
    "jira2mcp": REPO_ROOT / "packages" / "jira2mcp" / "pyproject.toml",
    "jira2cli": REPO_ROOT / "packages" / "jira2cli" / "pyproject.toml",
}
VERSION_PATTERN = re.compile(
    r'^(version\s*=\s*")(?P<version>\d+\.\d+\.\d+)("\s*)$', re.MULTILINE
)
SEMVER_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
LEGACY_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def supported_packages() -> tuple[str, ...]:
    return tuple(PACKAGE_PYPROJECT_PATHS)


def get_package_pyproject_path(package: str) -> Path:
    try:
        return PACKAGE_PYPROJECT_PATHS[package]
    except KeyError as exc:
        supported = ", ".join(supported_packages())
        msg = f"Unsupported package: {package}. Supported packages: {supported}"
        raise ValueError(msg) from exc


def read_pyproject(pyproject_path: Path) -> dict[str, Any]:
    return tomllib.loads(pyproject_path.read_text())


def read_current_version(pyproject_path: Path) -> str:
    data = read_pyproject(pyproject_path)
    return data["project"]["version"]


def read_package_version(package: str) -> str:
    return read_current_version(get_package_pyproject_path(package))


def parse_version(version: str) -> tuple[int, int, int]:
    match = SEMVER_PATTERN.fullmatch(version)
    if match is None:
        msg = f"Unsupported version format: {version}. Expected MAJOR.MINOR.PATCH"
        raise ValueError(msg)
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def bump_version(current_version: str, part: str) -> str:
    major, minor, patch = parse_version(current_version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def write_version(pyproject_path: Path, new_version: str) -> None:
    parse_version(new_version)
    content = pyproject_path.read_text()
    updated_content, replacements = VERSION_PATTERN.subn(
        rf"\g<1>{new_version}\3", content
    )
    if replacements != 1:
        msg = f"Could not uniquely update version in {pyproject_path}"
        raise RuntimeError(msg)
    if updated_content != content:
        pyproject_path.write_text(updated_content)


def parse_package_tag(tag: str) -> tuple[str, str]:
    if LEGACY_TAG_PATTERN.fullmatch(tag):
        msg = (
            f"Legacy tags like {tag} are not supported. "
            "Use <package>-vMAJOR.MINOR.PATCH instead."
        )
        raise ValueError(msg)
    if "-v" not in tag:
        msg = f"Unsupported tag format: {tag}. Expected <package>-vMAJOR.MINOR.PATCH"
        raise ValueError(msg)
    package, version = tag.rsplit("-v", 1)
    get_package_pyproject_path(package)
    parse_version(version)
    return package, version


def validate_tag(tag: str, package: str | None = None) -> tuple[str, str]:
    tagged_package, tagged_version = parse_package_tag(tag)
    if package is not None and package != tagged_package:
        msg = f"Package mismatch: --package {package} does not match tag package {tagged_package}"
        raise ValueError(msg)
    current_version = read_package_version(tagged_package)
    if current_version != tagged_version:
        msg = (
            f"Tag version {tagged_version} does not match {tagged_package} "
            f"pyproject version {current_version}"
        )
        raise ValueError(msg)
    return tagged_package, tagged_version


def validate_release_requirements(package: str) -> None:
    parse_version(read_package_version(package))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print, bump, or validate a package version."
    )
    parser.add_argument(
        "--package",
        choices=supported_packages(),
        help=(
            "Target package for --current, --version, --part, and --validate-release "
            f"(default: {DEFAULT_PACKAGE})."
        ),
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Print the selected package version and exit.",
    )
    parser.add_argument("--version", help="Set an explicit version such as 0.2.0.")
    parser.add_argument(
        "--part",
        choices=("patch", "minor", "major"),
        help="Version part to bump when not using --version (default: patch).",
    )
    parser.add_argument(
        "--validate-tag",
        metavar="TAG",
        help=(
            "Validate a package-specific tag like jira2mcp-v0.1.1. Parses the "
            "package from the tag, rejects legacy tags like v0.1.1, and checks "
            "that the tag version matches the package pyproject version."
        ),
    )
    parser.add_argument(
        "--validate-release",
        action="store_true",
        help="Validate release readiness for the selected package.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command_count = sum(
        bool(command)
        for command in (args.current, args.validate_tag, args.validate_release)
    )
    if command_count > 1:
        parser.error(
            "--current, --validate-tag, and --validate-release are mutually exclusive"
        )

    if (args.current or args.validate_tag or args.validate_release) and (
        args.version or args.part
    ):
        parser.error(
            "--version/--part can only be used when updating a package version"
        )

    try:
        if args.current:
            package = args.package or DEFAULT_PACKAGE
            print(read_package_version(package))
            return 0

        if args.validate_tag:
            package, version = validate_tag(args.validate_tag, args.package)
            print(f"{package}-v{version}")
            return 0

        if args.validate_release:
            package = args.package or DEFAULT_PACKAGE
            validate_release_requirements(package)
            print(f"{package} release validation passed")
            return 0

        package = args.package or DEFAULT_PACKAGE
        current_version = read_package_version(package)
        new_version = args.version or bump_version(
            current_version, args.part or "patch"
        )
        write_version(get_package_pyproject_path(package), new_version)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
