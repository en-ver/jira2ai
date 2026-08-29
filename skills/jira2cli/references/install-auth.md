# Install and Authenticate

`jira2cli` is a published **Jira Cloud-only** CLI. It requires Python >=3.13.

## Consumer Launch and Verification

Install [uv](https://docs.astral.sh/uv/) and run:

```sh
uvx jira2cli --help
```

Use the same `uvx jira2cli ...` prefix for the other commands in this skill. UVX runs the CLI but does not install or auto-discover the Pi skill.

## Repository-Local Maintainer Verification

From the repository root after workspace setup, maintainers can verify the checked-out CLI with:

```sh
uv sync --all-packages --group dev
uv run --locked --package jira2cli jira2cli --help
```

## Authentication

Supported credential modes:

1. Explicit CLI flag:
   - `uvx jira2cli --credentials-file <path> auth-status`
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

- `uvx jira2cli auth-status`
- `uvx jira2cli me --json`
- `uvx jira2cli projects --json`
- `uvx jira2cli projects --query <text> --json`

If verification fails, fix the environment values or the explicit credentials file instead of guessing or exposing the token.
