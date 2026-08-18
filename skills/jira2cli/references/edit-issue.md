# Edit an Issue

Use this only when the user has asked to change an existing Jira issue.

## Workflow

1. Read the current issue state:
   - `uvx jira2cli read <KEY> --json`
2. Fetch edit metadata before choosing fields to change:
   - `uvx jira2cli fields --issue-key <KEY> --json`
3. Inspect `required`, `allowedValues`, `schema`, `defaultValue`, and whether the target field is present for editing.
4. If a user field is involved, resolve likely identities first:
   - `uvx jira2cli users <query> --json`
5. Summarize the current values, intended edits, and exact `--fields-json` payload, plus any new summary or description text. Ask the user to confirm.
6. After confirmation only, run:
   - `uvx jira2cli edit <KEY> --summary <text> --description <text> --fields-json '<json>' --json`
7. If you need the untouched API payload instead of structured confirmation, rerun with `--raw` instead of `--json`.

Do not guess field IDs or values. If metadata does not show the field you need, stop and ask before editing.
