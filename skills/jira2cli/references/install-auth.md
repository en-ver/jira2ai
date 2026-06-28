# Install and Authenticate

`jira2cli` is currently documented in this repo as local/dev-only and **Jira Cloud only**.

## Supported Local Verification

From the repository root:

```sh
uv sync --all-packages --group dev
uv run --locked jira2cli --help
```

Use the same `uv run jira2cli ...` prefix for the other commands in this skill.

Do not claim or rely on `uvx jira2cli`, `pip install jira2cli`, or wheel/PyPI install paths unless the repo docs change first.

## Authentication

Supported credential modes:

1. Explicit CLI flag:
   - `uv run jira2cli --credentials-file <path> auth-status`
2. Environment variables when the flag is omitted:
   - `JIRA_URL=https://<site>.atlassian.net`
   - `JIRA_USER=<email>`
   - `JIRA_API_TOKEN=<api-token>`

Credentials file shape:

```json
{
  "url": "https://<site>.atlassian.net",
  "username": "<email>",
  "api_token": "<api-token>"
}
```

Rules:

- If `--credentials-file` is omitted, `jira2cli` uses the environment variables.
- There is no default credentials path.
- There is no implicit `JIRA_CREDENTIALS_FILE` behavior.
- Keep `JIRA_API_TOKEN` in a local environment file, secret manager, or interactive secret prompt.
- Never print `JIRA_API_TOKEN`, paste it into chat, or commit it to the repo.
- Keep `JIRA_URL` as the full Jira Cloud base URL, including `https://`.

## Read-Only Verification

After the environment is configured, verify access with a non-mutating command such as:

- `uv run --locked jira2cli auth-status`
- `uv run --locked jira2cli me --json`
- `uv run --locked jira2cli projects --json`
- `uv run --locked jira2cli projects --query <text> --json`

If verification fails, fix the environment values or the explicit credentials file instead of guessing or exposing the token.
