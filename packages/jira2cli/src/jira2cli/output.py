"""CLI rendering and error helpers for jira2cli."""

from __future__ import annotations

import json
from typing import Any, NoReturn

import typer
from jira2py.helpers import HelperResult
from jira2py.helpers.errors import JiraHelperError, JiraHelperValidationError


def render_operation_result(
    result: HelperResult,
    *,
    json_output: bool = False,
    raw_output: bool = False,
) -> str:
    """Render an operation result for CLI stdout."""
    if json_output or raw_output:
        return json.dumps(
            _json_payload(result),
            indent=2,
            sort_keys=True,
            default=str,
        )
    return result.text


def _json_payload(result: HelperResult) -> Any:
    """Select the most structured payload available for JSON output."""
    if result.data is not None:
        return result.data

    if result.raw_content is None:
        return result.text

    try:
        return json.loads(result.raw_content)
    except json.JSONDecodeError:
        return result.raw_content


def format_cli_error(error: JiraHelperError) -> str:
    """Format a helper error for CLI stderr."""
    if not error.details:
        return error.message

    return (
        f"{error.message}\n"
        f"Details:\n{json.dumps(error.details, indent=2, sort_keys=True, default=str)}"
    )


def error_exit_code(error: JiraHelperError) -> int:
    """Return the CLI exit code for a helper error."""
    if isinstance(error, JiraHelperValidationError):
        return 2
    return 1


def raise_cli_usage_error(
    message: str,
    *,
    param_hint: str | None = None,
) -> NoReturn:
    """Write a CLI usage error to stderr and exit with code 2."""
    if param_hint:
        typer.echo(f"{param_hint}: {message}", err=True)
    else:
        typer.echo(message, err=True)
    raise typer.Exit(code=2)


def validate_output_options(*, json_output: bool, raw_output: bool) -> None:
    """Reject conflicting structured output flags."""
    if json_output and raw_output:
        raise_cli_usage_error(
            "Use only one of --json or --raw.",
            param_hint="--json / --raw",
        )


def raise_cli_error(error: JiraHelperError) -> NoReturn:
    """Write a CLI-friendly helper error message to stderr and exit."""
    typer.echo(format_cli_error(error), err=True)
    raise typer.Exit(code=error_exit_code(error))


def raise_cli_exception(error: Exception) -> NoReturn:
    """Write a CLI-friendly error message to stderr and exit."""
    if isinstance(error, JiraHelperError):
        raise_cli_error(error)

    typer.echo(str(error), err=True)
    raise typer.Exit(code=1)


__all__ = [
    "error_exit_code",
    "format_cli_error",
    "raise_cli_error",
    "raise_cli_exception",
    "raise_cli_usage_error",
    "render_operation_result",
    "validate_output_options",
]
