from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

import mcp.types as mcp_types
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from jira2mcp import mcp

if TYPE_CHECKING:
    from .conftest import JiraE2EConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
STDIO_COMMAND = "uv"
STDIO_ARGS = [
    "--directory",
    str(REPO_ROOT),
    "run",
    "--package",
    "jira2mcp",
    "jira2mcp",
]
CREATE_FIELDS_OVERRIDE_ENV_VAR = "JIRA_E2E_CREATE_FIELDS_JSON"
_CREATE_FIELD_WRAPPER_KEY = "data"
_CREATE_FIELD_RESERVED_IDS = frozenset(
    {"description", "issuetype", "project", "summary"}
)
_PREFERRED_ALLOWED_VALUE_NAMES: dict[str, tuple[str, ...]] = {
    "Requester Team": ("Product Team",),
    "Stream": ("Strategic",),
    "Team": ("Back-End",),
}
_MISSING = object()


def inmemory_client_mcp(*, timeout: float | int | None = None) -> Client:
    return Client(mcp, timeout=timeout)


def stdio_transport_mcp(
    *,
    credentials_file: Path,
    cwd: str | Path | None = None,
    log_file: Path | TextIO | None = None,
) -> StdioTransport:
    return StdioTransport(
        command=STDIO_COMMAND,
        args=[*STDIO_ARGS, "--credentials-file", str(credentials_file.resolve())],
        env=None,
        cwd=str(cwd) if cwd is not None else None,
        keep_alive=False,
        log_file=log_file,
    )


def stdio_client_mcp(
    *,
    credentials_file: Path,
    cwd: str | Path | None = None,
    log_file: Path | TextIO | None = None,
    timeout: float | int | None = None,
) -> Client:
    return Client(
        stdio_transport_mcp(
            credentials_file=credentials_file,
            cwd=cwd,
            log_file=log_file,
        ),
        timeout=timeout,
    )


async def list_tools_mcp(client: Client) -> mcp_types.ListToolsResult:
    return await client.list_tools_mcp()


async def call_tool_mcp(
    client: Client,
    name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    timeout: float | int | None = None,
) -> mcp_types.CallToolResult:
    return await client.call_tool_mcp(
        name,
        dict(arguments or {}),
        timeout=timeout,
    )


async def list_resources_mcp(client: Client) -> mcp_types.ListResourcesResult:
    return await client.list_resources_mcp()


async def read_resource_mcp(
    client: Client,
    uri: str,
) -> mcp_types.ReadResourceResult:
    return await client.read_resource_mcp(uri)


async def list_prompts_mcp(client: Client) -> mcp_types.ListPromptsResult:
    return await client.list_prompts_mcp()


async def get_prompt_mcp(
    client: Client,
    name: str,
    arguments: Mapping[str, Any] | None = None,
) -> mcp_types.GetPromptResult:
    return await client.get_prompt_mcp(name, dict(arguments or {}))


def assert_non_error_result(
    result: mcp_types.CallToolResult,
) -> mcp_types.CallToolResult:
    if result.isError:
        message = joined_text_content(result)
        raise AssertionError(message or "MCP tool call returned isError=True")
    return result


def structured_content(
    result: mcp_types.CallToolResult,
) -> Any:
    return result.structuredContent


def assert_structured_content(
    result: mcp_types.CallToolResult,
    expected_type: type[Any] | tuple[type[Any], ...] = dict,
) -> Any:
    value = structured_content(result)
    if value is None:
        raise AssertionError("Expected structured content but result had none")
    if not isinstance(value, expected_type):
        raise AssertionError(
            "Expected structured content of type "
            f"{_type_label(expected_type)}, got {type(value).__name__}"
        )
    return value


def text_content_blocks(result: mcp_types.CallToolResult) -> list[str]:
    return _texts_from_content_blocks(result.content)


def require_text_content(result: mcp_types.CallToolResult) -> str:
    texts = text_content_blocks(result)
    if not texts:
        raise AssertionError("Expected text content but result had none")
    return "\n".join(texts)


def joined_text_content(result: mcp_types.CallToolResult) -> str:
    return "\n".join(text_content_blocks(result))


def parse_json_text(text: str) -> Any:
    return json.loads(text)


def parse_result_json(result: mcp_types.CallToolResult) -> Any:
    return parse_json_text(require_text_content(result))


def assert_result_data(
    result: mcp_types.CallToolResult,
    expected_type: type[Any] | tuple[type[Any], ...],
) -> Any:
    value = structured_content(result)
    if value is not None:
        unwrapped = _unwrap_result_data(value, expected_type)
        if isinstance(unwrapped, expected_type):
            return unwrapped

    parsed = _unwrap_result_data(parse_result_json(result), expected_type)
    if not isinstance(parsed, expected_type):
        raise AssertionError(
            "Expected raw result data of type "
            f"{_type_label(expected_type)}, got {type(parsed).__name__}"
        )
    return parsed


async def metadata_create_fields_mcp(
    client: Client,
    project_key: str,
    issue_type: str,
) -> list[Mapping[str, Any]]:
    result = assert_non_error_result(
        await call_tool_mcp(
            client,
            "jira_fields",
            {
                "project_key": project_key,
                "issue_type": issue_type,
                "raw": True,
            },
        )
    )
    return _assert_mapping_sequence(
        assert_result_data(result, list),
        description="jira_fields raw payload",
    )


async def metadata_users_mcp(
    client: Client,
    query: str,
) -> list[Mapping[str, Any]]:
    result = assert_non_error_result(
        await call_tool_mcp(
            client,
            "jira_users",
            {"query": query, "raw": True},
        )
    )
    return _assert_mapping_sequence(
        assert_result_data(result, list),
        description="jira_users raw payload",
    )


async def build_create_fields_from_metadata_mcp(
    client: Client,
    config: JiraE2EConfig,
) -> dict[str, Any]:
    field_metadata = await metadata_create_fields_mcp(
        client,
        config.project_key,
        config.issue_type,
    )
    overrides = _load_create_field_overrides(field_metadata)
    create_fields: dict[str, Any] = {}
    unresolved: list[str] = []
    reporter_account_id: str | None = None

    for field in field_metadata:
        if not field.get("required"):
            continue

        field_id = _resolved_field_id(field)
        if field_id is None or field_id in _CREATE_FIELD_RESERVED_IDS:
            continue

        if field_id in overrides:
            create_fields[field_id] = overrides.pop(field_id)
            continue

        value = _selected_value_from_field_metadata(field)
        if value is _MISSING and _schema_target_type(field) == "user":
            if reporter_account_id is None:
                reporter_query = config.user_query or config.jira_user
                reporter_account_id = _resolve_user_account_id(
                    await metadata_users_mcp(client, reporter_query),
                    reporter_query,
                )
            if reporter_account_id is not None:
                value = {"accountId": reporter_account_id}

        if value is _MISSING:
            unresolved.append(_field_label(field))
            continue

        create_fields[field_id] = value

    reserved_overrides = sorted(
        key for key in overrides if key in _CREATE_FIELD_RESERVED_IDS
    )
    if reserved_overrides:
        raise AssertionError(
            f"{CREATE_FIELDS_OVERRIDE_ENV_VAR} must not override reserved jira_create "
            f"fields: {reserved_overrides}"
        )

    create_fields.update(overrides)

    if unresolved:
        raise AssertionError(
            "Could not infer required jira_create fields from jira_fields metadata: "
            f"{', '.join(unresolved)}. Set {CREATE_FIELDS_OVERRIDE_ENV_VAR} with a "
            "JSON object of explicit field values if your Jira schema needs overrides."
        )

    return create_fields


def resource_text_blocks(result: mcp_types.ReadResourceResult) -> list[str]:
    return [
        content.text
        for content in result.contents
        if isinstance(content, mcp_types.TextResourceContents)
    ]


def require_resource_text(result: mcp_types.ReadResourceResult) -> str:
    texts = resource_text_blocks(result)
    if not texts:
        raise AssertionError("Expected text resource contents but found none")
    return "\n".join(texts)


def prompt_text_blocks(result: mcp_types.GetPromptResult) -> list[str]:
    return [
        message.content.text
        for message in result.messages
        if isinstance(message.content, mcp_types.TextContent)
    ]


def require_prompt_text(result: mcp_types.GetPromptResult) -> str:
    texts = prompt_text_blocks(result)
    if not texts:
        raise AssertionError("Expected prompt text but prompt had none")
    return "\n".join(texts)


def tool_names(result: mcp_types.ListToolsResult) -> list[str]:
    return [tool.name for tool in result.tools]


def resource_uris(result: mcp_types.ListResourcesResult) -> list[str]:
    return [str(resource.uri) for resource in result.resources]


def prompt_names(result: mcp_types.ListPromptsResult) -> list[str]:
    return [prompt.name for prompt in result.prompts]


def assert_contains_names(
    actual_names: Sequence[str],
    expected_names: Sequence[str],
) -> None:
    missing = [name for name in expected_names if name not in actual_names]
    if missing:
        raise AssertionError(
            f"Missing expected names: {missing}. Actual names: {list(actual_names)}"
        )


def _assert_mapping_sequence(
    values: Sequence[Any],
    *,
    description: str,
) -> list[Mapping[str, Any]]:
    normalized: list[Mapping[str, Any]] = []
    for value in values:
        if not isinstance(value, Mapping):
            raise AssertionError(
                f"Expected every item in {description} to be a mapping"
            )
        normalized.append(value)
    return normalized


def _unwrap_result_data(
    value: Any,
    expected_type: type[Any] | tuple[type[Any], ...],
) -> Any:
    if isinstance(value, expected_type):
        return value
    if (
        isinstance(value, Mapping)
        and len(value) == 1
        and _CREATE_FIELD_WRAPPER_KEY in value
    ):
        wrapped = value[_CREATE_FIELD_WRAPPER_KEY]
        if isinstance(wrapped, expected_type):
            return wrapped
    return value


def _load_create_field_overrides(
    field_metadata: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    raw_overrides = os.getenv(CREATE_FIELDS_OVERRIDE_ENV_VAR)
    if raw_overrides is None or raw_overrides.strip() == "":
        return {}

    try:
        parsed = json.loads(raw_overrides)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{CREATE_FIELDS_OVERRIDE_ENV_VAR} must be valid JSON: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise AssertionError(
            f"{CREATE_FIELDS_OVERRIDE_ENV_VAR} must decode to a JSON object"
        )

    aliases: dict[str, str] = {}
    for field in field_metadata:
        field_id = _resolved_field_id(field)
        if field_id is None:
            continue
        aliases[field_id] = field_id
        name = field.get("name")
        if isinstance(name, str) and name:
            aliases[name] = field_id
            aliases[name.lower()] = field_id

    overrides: dict[str, Any] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            raise AssertionError(
                f"{CREATE_FIELDS_OVERRIDE_ENV_VAR} keys must be strings"
            )
        resolved_key = aliases.get(key) or aliases.get(key.lower()) or key
        overrides[resolved_key] = value
    return overrides


def _resolved_field_id(field: Mapping[str, Any]) -> str | None:
    for key in ("fieldId", "key", "id"):
        value = field.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _field_label(field: Mapping[str, Any]) -> str:
    field_id = _resolved_field_id(field) or "?"
    name = field.get("name")
    if isinstance(name, str) and name:
        return f'{field_id} "{name}"'
    return field_id


def _selected_value_from_field_metadata(field: Mapping[str, Any]) -> Any:
    default_value = field.get("defaultValue")
    if default_value is not None:
        return _canonicalize_field_value(default_value, field)

    allowed_values = field.get("allowedValues")
    if not isinstance(allowed_values, list) or not allowed_values:
        return _MISSING

    selected = _choose_allowed_value(field, allowed_values)
    if selected is _MISSING:
        return _MISSING
    return _canonicalize_field_value(selected, field)


def _choose_allowed_value(
    field: Mapping[str, Any],
    allowed_values: Sequence[Any],
) -> Any:
    available = [
        value
        for value in allowed_values
        if not (isinstance(value, Mapping) and value.get("disabled") is True)
    ]
    if not available:
        return _MISSING

    field_name = field.get("name")
    preferred_names = (
        _PREFERRED_ALLOWED_VALUE_NAMES.get(field_name, ())
        if isinstance(field_name, str)
        else ()
    )
    for preferred_name in preferred_names:
        for value in available:
            if _allowed_value_label(value).casefold() == preferred_name.casefold():
                return value

    return min(
        available,
        key=lambda value: (
            _allowed_value_label(value).casefold(),
            json.dumps(value, sort_keys=True, default=str),
        ),
    )


def _allowed_value_label(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("name", "value", "displayName", "key", "accountId"):
            selected = value.get(key)
            if isinstance(selected, str) and selected:
                return selected
    return json.dumps(value, sort_keys=True, default=str)


def _canonicalize_field_value(
    value: Any,
    field: Mapping[str, Any],
) -> Any:
    schema_type, item_type = _field_schema(field)
    if schema_type == "array":
        raw_items = value if isinstance(value, list) else [value]
        if not raw_items:
            return _MISSING
        normalized = [
            _canonicalize_single_value(item, target_type=item_type)
            for item in raw_items
        ]
        if any(item is _MISSING for item in normalized):
            return _MISSING
        return normalized
    return _canonicalize_single_value(value, target_type=schema_type)


def _canonicalize_single_value(value: Any, *, target_type: str | None) -> Any:
    if target_type == "user":
        if isinstance(value, str) and value:
            return {"accountId": value}
        if isinstance(value, Mapping):
            account_id = value.get("accountId")
            if isinstance(account_id, str) and account_id:
                return {"accountId": account_id}
        return _MISSING

    preferred_keys = {
        "component": ("id", "name"),
        "issuetype": ("id", "name"),
        "option": ("id", "value", "name"),
        "priority": ("id", "name"),
        "project": ("id", "key"),
        "version": ("id", "name"),
    }.get(target_type, ("id", "key", "name", "value", "accountId"))

    if isinstance(value, Mapping):
        for key in preferred_keys:
            selected = value.get(key)
            if selected is not None and selected != "":
                return {key: selected}
        return _MISSING

    return value


def _field_schema(field: Mapping[str, Any]) -> tuple[str, str | None]:
    schema = field.get("schema")
    if not isinstance(schema, Mapping):
        return "unknown", None

    schema_type = schema.get("type")
    item_type = schema.get("items")
    return (
        schema_type if isinstance(schema_type, str) and schema_type else "unknown",
        item_type if isinstance(item_type, str) and item_type else None,
    )


def _schema_target_type(field: Mapping[str, Any]) -> str:
    schema_type, item_type = _field_schema(field)
    if schema_type == "array" and item_type is not None:
        return item_type
    return schema_type


def _resolve_user_account_id(
    users: Sequence[Mapping[str, Any]],
    query: str,
) -> str | None:
    normalized_query = query.strip().casefold()

    for key in ("emailAddress", "displayName", "accountId"):
        for user in users:
            candidate = user.get(key)
            account_id = user.get("accountId")
            if not isinstance(candidate, str) or not isinstance(account_id, str):
                continue
            if candidate.casefold() == normalized_query:
                return account_id

    active_users = [
        user
        for user in users
        if isinstance(user.get("accountId"), str) and user.get("active") is not False
    ]
    if active_users:
        selected = min(
            active_users,
            key=lambda user: (
                str(user.get("displayName", "")).casefold(),
                str(user.get("accountId", "")),
            ),
        )
        return str(selected.get("accountId"))

    for user in users:
        account_id = user.get("accountId")
        if isinstance(account_id, str) and account_id:
            return account_id
    return None


def _texts_from_content_blocks(content: Sequence[Any]) -> list[str]:
    return [block.text for block in content if isinstance(block, mcp_types.TextContent)]


def _type_label(expected_type: type[Any] | tuple[type[Any], ...]) -> str:
    if isinstance(expected_type, tuple):
        return " | ".join(tp.__name__ for tp in expected_type)
    return expected_type.__name__


__all__ = [
    "CREATE_FIELDS_OVERRIDE_ENV_VAR",
    "REPO_ROOT",
    "STDIO_ARGS",
    "STDIO_COMMAND",
    "assert_contains_names",
    "assert_non_error_result",
    "assert_result_data",
    "assert_structured_content",
    "build_create_fields_from_metadata_mcp",
    "call_tool_mcp",
    "get_prompt_mcp",
    "inmemory_client_mcp",
    "joined_text_content",
    "list_prompts_mcp",
    "list_resources_mcp",
    "list_tools_mcp",
    "metadata_create_fields_mcp",
    "metadata_users_mcp",
    "parse_json_text",
    "parse_result_json",
    "prompt_names",
    "prompt_text_blocks",
    "read_resource_mcp",
    "require_prompt_text",
    "require_resource_text",
    "require_text_content",
    "resource_text_blocks",
    "resource_uris",
    "stdio_client_mcp",
    "stdio_transport_mcp",
    "structured_content",
    "text_content_blocks",
    "tool_names",
]
