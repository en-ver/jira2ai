from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"
VERSION_PATTERN = re.compile(
    r'^(version\s*=\s*")(?P<version>\d+\.\d+\.\d+)("\s*)$', re.MULTILINE
)
SEMVER_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


def read_current_version(pyproject_path: Path) -> str:
    data = tomllib.loads(pyproject_path.read_text())
    return data["project"]["version"]


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
        rf"\g<1>{new_version}\3", content, count=1
    )
    if replacements != 1:
        msg = f"Could not uniquely update version in {pyproject_path}"
        raise RuntimeError(msg)
    if updated_content != content:
        pyproject_path.write_text(updated_content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump or print the project version.")
    parser.add_argument(
        "--current", action="store_true", help="Print the current version and exit."
    )
    parser.add_argument("--version", help="Set an explicit version such as 0.2.0.")
    parser.add_argument(
        "--part",
        choices=("patch", "minor", "major"),
        default="patch",
        help="Version part to bump when --version is not provided (default: patch).",
    )
    args = parser.parse_args()

    if args.current and args.version:
        parser.error("--current cannot be combined with --version")

    current_version = read_current_version(PYPROJECT_PATH)

    if args.current:
        print(current_version)
        return 0

    try:
        new_version = args.version or bump_version(current_version, args.part)
        write_version(PYPROJECT_PATH, new_version)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
