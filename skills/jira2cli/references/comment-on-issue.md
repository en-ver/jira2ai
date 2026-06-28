# Comment Management

Use this when the user wants to add, update, or delete a comment on an existing Jira issue.

## Workflow

1. Read the current issue:
   - `uv run jira2cli read <KEY> --json`
2. Review the existing discussion first:
   - `uv run jira2cli comments <KEY> --json`
3. If the thread is long, page or reorder comment reads before drafting the reply:
   - `uv run jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
4. Capture the exact target comment ID before update or delete actions.
5. Draft the exact body change or deletion target and summarize it.
6. Ask the user to confirm the target issue, comment ID when applicable, and final body.

## Add a Comment

After confirmation only, run:

- `uv run jira2cli comment <KEY> <BODY> --json`

## Update a Comment

After confirmation only, run:

- `uv run jira2cli comment-update <KEY> <COMMENT_ID> <BODY> --json`

## Delete a Comment

After confirmation only, run:

- `uv run jira2cli comment-delete <KEY> <COMMENT_ID> --json`

Use `--raw` instead of `--json` only when you need the untouched API payload.

Do not post, overwrite, or delete a comment before checking the current issue and recent comments.
