# User Identity Lookup

Use this when metadata or current issue state shows that a Jira user field needs a specific person.

## Workflow

1. Confirm which field needs a user value from metadata or the current issue:
   - `uv run jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
   - `uv run jira2cli fields --issue-key <KEY> --json`
   - `uv run jira2cli read <KEY> --json`
2. Search for likely identities:
   - `uv run jira2cli users <query>`
3. Prefer structured output when you need account IDs or exact display names, and raise `--max-results` if you need a wider candidate set:
   - `uv run jira2cli users <query> --max-results <N> --json`
4. Summarize the candidate identity and ask the user to confirm it before any mutation.

`jira2cli users <query>` is identity lookup only. It does not prove the user is assignable to the project or issue unless the later `jira2cli` operation or its output confirms it.
