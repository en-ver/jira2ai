# `jira2mcp` standalone MCP E2E tests

These tests cover the local `jira2mcp` FastMCP server only.

- No automated CLI calls
- No CLI-vs-MCP comparisons
- Default test runs exclude all `mcp_live` tests

## Test modules

- `test_live_inmemory.py` - broad live coverage with in-memory `Client(mcp)`
- `test_live_stdio.py` - stdio smoke tests against the local checkout
- `test_live_write.py` - opt-in live write scenarios

## Environment

Required for any live run:

- `JIRA_URL`
- `JIRA_USER`
- `JIRA_API_TOKEN`

Optional fixtures/defaults:

- `JIRA_E2E_PROJECT_KEY` - default `PR`
- `JIRA_E2E_ISSUE_TYPE` - default `Task`
- `JIRA_E2E_LABEL` - default `jira2py-e2e`
- `JIRA_E2E_ISSUE_KEY` - pins `jira_read` / `jira_comments`
- `JIRA_E2E_USER_QUERY` - overrides the default `jira_users` query (`JIRA_USER`)
- `JIRA_E2E_WORKLOG_ISSUE_KEY` - preferred worklog target
- `JIRA_E2E_ATTACHMENT_ID` - optional existing attachment fixture for download coverage
- `JIRA_E2E_CREATE_FIELDS_JSON` - optional JSON object to override or supplement metadata-derived `jira_create` fields for site-specific required fields
- `JIRA_E2E_ALLOW_WRITE=1` - required for `mcp_write` tests

Without credentials, live tests skip cleanly. Optional issue/worklog/attachment scenarios also skip cleanly when their fixture env vars are absent and discovery is not possible.

## Commands

Non-live default validation:

```bash
make test
```

Read-only live in-memory + stdio selection:

```bash
make test-mcp-e2e
make test-mcp-e2e-stdio
```

Direct pytest equivalents:

```bash
uv run --locked python -m pytest tests/e2e/jira2mcp_e2e -m "mcp_live and not mcp_write"
uv run --locked python -m pytest tests/e2e/jira2mcp_e2e -m "mcp_live and mcp_stdio and not mcp_write"
```

Opt-in write tests:

```bash
JIRA_E2E_ALLOW_WRITE=1 make test-mcp-e2e-write
# or
JIRA_E2E_ALLOW_WRITE=1 uv run --locked python -m pytest tests/e2e/jira2mcp_e2e/test_live_write.py -m "mcp_live and mcp_write"
```

## Write-test behavior

`test_live_write.py` is intentionally opt-in.

When enabled it first calls `jira_fields(..., raw=True)` to discover required create-screen metadata, then builds `jira_create` fields dynamically. The default path now handles the current `PR` / `Task` schema, including required `components`, `Requester Team`, `Stream`, `Team`, and `reporter`, and still labels created issues `jira2py-e2e`.

Post-create `jira_search` assertions use a short bounded retry because live Jira indexing can lag immediately after issue creation. If the issues still do not appear before the timeout, the test fails with the expected keys and the last observed search payload.

If your Jira site needs a different required-field choice, set `JIRA_E2E_CREATE_FIELDS_JSON` to a JSON object keyed by field ID or field name. Example:

```bash
export JIRA_E2E_CREATE_FIELDS_JSON='{
  "Team": [{"id": "14648"}],
  "customfield_11577": {"id": "14517"}
}'
```

Attachment coverage is download-only and runs only when `JIRA_E2E_ATTACHMENT_ID` points to an existing attachment. The tests do not upload or invent attachments.

## Stdio scope

The stdio smoke tests launch the local checkout only:

```bash
uv --directory /Users/enver/github/personal/jira2ai run jira2mcp
```

They do not use `uvx`.

## Raw-list regression coverage

List-shaped raw outputs are now regression-covered.

- `jira_fields(project_key=..., issue_type=..., raw=True)`
- `jira_users(query=..., raw=True)`

The tests assert that MCP `structuredContent` stays dict-shaped and carries the original list under `data`, while text content remains the original JSON list.

## Human-only manual CLI spot checks

If you want extra confidence outside pytest, run manual CLI spot checks yourself. Keep them separate from this suite. Example ideas:

- `uv run jira2cli read PR-123`
- `uv run jira2cli search 'project = PR ORDER BY created DESC'`

These are notes only; the automated E2E tests never call the CLI.
