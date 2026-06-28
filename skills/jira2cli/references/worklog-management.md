# Worklog Management

Use this when the user wants to inspect or mutate worklogs on a specific Jira issue.

## Workflow

1. Read the current issue:
   - `uv run jira2cli read <KEY> --json`
2. List current worklogs and capture the exact worklog ID when needed:
   - `uv run jira2cli worklogs <KEY> --json`
3. Summarize the exact issue key, worklog ID when applicable, time-spent value, optional started timestamp, and optional comment.
4. Ask the user to confirm before any add, update, or delete action.

## Add a worklog

After confirmation only, run:

- `uv run jira2cli worklog-add <KEY> '1h 30m' --started <TIMESTAMP> --comment <TEXT> --json`

## Update a worklog

After confirmation only, run:

- `uv run jira2cli worklog-update <KEY> <WORKLOG_ID> --time-spent '45m' --started <TIMESTAMP> --comment <TEXT> --json`

## Delete a worklog

After confirmation only, run:

- `uv run jira2cli worklog-delete <KEY> <WORKLOG_ID> --json`

Use `--raw` instead of `--json` only when you need the untouched API payload.

Do not guess worklog IDs or mutate time tracking without explicit confirmation.
