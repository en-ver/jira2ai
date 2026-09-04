# Create an Issue

Use this only when the user has asked for a new Jira issue.

## Workflow

1. Resolve and confirm the target project:
   - `uvx jira2cli projects --query <text> --json`
2. Resolve available issue types, then fetch scoped create metadata:
   - `uvx jira2cli fields --project-key <PROJECT> --json`
   - `uvx jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
3. Inspect `required`, `allowedValues`, `schema`, `defaultValue`, and any relevant extra Jira properties before choosing field values.
4. If a user field is needed, resolve identities first:
   - `uvx jira2cli users <query> --json`
5. Build only the fields Jira requires or the user explicitly requested, and keep them in `--fields-json '<json>'`.
6. Summarize the chosen project, issue type, summary, description, and exact field choices. Ask the user to confirm.
7. After confirmation only, run:
   - `uvx jira2cli create <PROJECT> <TYPE> <SUMMARY> --description <text> --fields-json '<json>' --json`
8. If you need API-oriented output instead of structured confirmation, rerun with `--raw` instead of `--json`. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes.

## Rich-text mentions

`--description` and string values in compatible rich-text `--fields-json` fields recognize canonical `[~accountId:<id>]` as one semantic ADF mention; Jira may notify that account. Escaped, malformed, code, link, and image forms remain text. Preserve raw issue ADF from `read --json` for identity-safe later edits, because formatted Markdown is presentation-only and can lose mention identity when written back.

Do not guess required fields or send placeholder values just to make the create succeed.
