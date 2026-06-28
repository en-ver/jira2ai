# Link Issues

Use this when the user wants to inspect, add, or remove a relationship between Jira issues.

## Workflow

1. Read the issue first when you need current links:
   - `uv run jira2cli read <KEY> --json`
2. List issue links directly when you need a focused link view:
   - `uv run jira2cli issue-links <KEY> --json`
3. Read both issues before changing links:
   - `uv run jira2cli read <OUTWARD_KEY> --json`
   - `uv run jira2cli read <INWARD_KEY> --json`
4. Discover valid link types:
   - `uv run jira2cli link-types --json`
5. Confirm the exact link type and direction. Use the outward and inward labels from the link type output to decide which issue key belongs in each position.
6. Summarize the keys, the chosen type, and the chosen direction. Ask the user to confirm.

## Add a Link

After confirmation only, run:

- `uv run jira2cli add-link <LINK_TYPE> <OUTWARD_KEY> <INWARD_KEY> --json`

## Delete an Existing Link

1. Use `issue-links` or issue read output to capture the exact existing link ID.
2. Confirm the link ID and the relationship it represents.
3. After confirmation only, run:
   - `uv run jira2cli delete-link <LINK_ID> --json`

Use `--raw` instead of `--json` only when you need the untouched API payload.

Never guess link direction or delete a link by description alone.
