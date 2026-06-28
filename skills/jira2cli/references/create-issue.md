# Create an Issue

Use this only when the user has asked for a new Jira issue.

## Workflow

1. Resolve and confirm the target project:
   - `uv run jira2cli projects --query <text> --json`
2. Resolve available issue types, then fetch scoped create metadata:
   - `uv run jira2cli fields --project-key <PROJECT> --json`
   - `uv run jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
3. Inspect `required`, `allowedValues`, `schema`, `defaultValue`, and any relevant extra Jira properties before choosing field values.
4. If a user field is needed, resolve identities first:
   - `uv run jira2cli users <query> --json`
5. Build only the fields Jira requires or the user explicitly requested, and keep them in `--fields-json '<json>'`.
6. Summarize the chosen project, issue type, summary, description, and exact field choices. Ask the user to confirm.
7. After confirmation only, run:
   - `uv run jira2cli create <PROJECT> <TYPE> <SUMMARY> --description <text> --fields-json '<json>' --json`
8. If you need the untouched API payload instead of structured confirmation, rerun with `--raw` instead of `--json`.

Do not guess required fields or send placeholder values just to make the create succeed.
