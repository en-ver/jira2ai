"""Smoke-test an installed jira2mcp wheel outside its source checkout."""

from __future__ import annotations

import argparse
import asyncio
from importlib.metadata import distribution, version
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from packaging.specifiers import SpecifierSet
from packaging.version import Version

EXPECTED_TOOL_COUNT = 37
REGISTRY_PACKAGES = ("fastmcp", "jira2py")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--fastmcp-specifier", required=True)
    return parser.parse_args()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


async def _list_tools_over_stdio(server: Path) -> list[str]:
    parameters = StdioServerParameters(command=str(server))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            response = await session.list_tools()
    return sorted(tool.name for tool in response.tools)


def main() -> None:
    args = _parse_args()

    import jira2mcp

    package_path = Path(jira2mcp.__file__).resolve()
    checkout = args.checkout.resolve()
    if _is_within(package_path, checkout):
        raise AssertionError(f"jira2mcp was imported from the checkout: {package_path}")

    fastmcp_version = Version(version("fastmcp"))
    if fastmcp_version not in SpecifierSet(args.fastmcp_specifier):
        raise AssertionError(
            f"fastmcp {fastmcp_version} does not satisfy {args.fastmcp_specifier}"
        )

    for package_name in REGISTRY_PACKAGES:
        if distribution(package_name).read_text("direct_url.json") is not None:
            raise AssertionError(f"{package_name} was not installed from the registry")

    server = args.server.resolve()
    if _is_within(server, checkout):
        raise AssertionError(f"jira2mcp server is inside the checkout: {server}")

    names = asyncio.run(_list_tools_over_stdio(server))
    if len(names) != EXPECTED_TOOL_COUNT:
        raise AssertionError(
            f"Expected {EXPECTED_TOOL_COUNT} tools, got {len(names)}: {names}"
        )
    if any(not name.startswith("jira_") for name in names):
        raise AssertionError(f"Unexpected non-Jira tool names: {names}")

    print(f"jira2mcp {version('jira2mcp')} with FastMCP {fastmcp_version}")
    print(f"Listed {len(names)} tools: {', '.join(names)}")


if __name__ == "__main__":
    main()
