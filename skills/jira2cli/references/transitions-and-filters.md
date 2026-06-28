# Transitions and Saved Filters

Use this when you need workflow transition metadata, need to apply a transition, or want to discover/run saved Jira filters.

## Workflow transitions

1. Read the issue first:
   - `uv run jira2cli read <KEY> --json`
2. List the available transitions:
   - `uv run jira2cli transitions <KEY> --json`
3. Confirm the exact transition ID or exact transition name.
4. After confirmation only, run:
   - `uv run jira2cli transition <KEY> <TRANSITION_ID_OR_NAME> --json`

Do not guess transition names or assume a workflow state exists in the target project.

## Saved filters

1. List visible filters:
   - `uv run jira2cli filters --json`
2. Narrow by name when needed:
   - `uv run jira2cli filters --query <text> --json`
3. Capture the exact saved filter ID before running it.
4. Run the filter through the normal search flow:
   - `uv run jira2cli filter-run <FILTER_ID> --field key --field summary --json`
5. Add repeated `--field` options when you need more search fields.

`filter-run` returns the same search-shaped result as `search` after resolving the saved filter's JQL.
