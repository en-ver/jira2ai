# Project Discovery

Use this to resolve the exact Jira project key before searching, creating, or editing issues.

## Workflow

1. List accessible projects:
   - `uv run jira2cli projects --json`
2. Narrow by name or key text when the user gives an approximate project name:
   - `uv run jira2cli projects --query <text> --json`
3. Confirm the exact project key and project name with the user before any later operation depends on it.
4. If the issue type is still unknown, use discovery mode to inspect the project's available issue types:
   - `uv run jira2cli fields --project-key <PROJECT> --json`
5. Only after the issue type is known, fetch scoped create metadata:
   - `uv run jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`

Summarize the chosen project key before moving on to metadata lookup or issue mutations.
