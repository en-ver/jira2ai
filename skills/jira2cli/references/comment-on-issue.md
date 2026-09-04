# Comment Management

Use this when the user wants to add, update, or delete a comment on an existing Jira issue.

## Workflow

1. Read the current issue:
   - `uvx jira2cli read <KEY> --fields summary,status --json`
2. Review the existing discussion first:
   - `uvx jira2cli comments <KEY> --json`
3. If the thread is long, page or reorder comment reads before drafting the reply:
   - `uvx jira2cli comments <KEY> --start-at <N> --max-results <N> --order-by -created --json`
4. Capture the exact target comment ID before update or delete actions.
5. Draft the exact body change or deletion target and summarize it.
6. Ask the user to confirm the target issue, comment ID when applicable, and final body.

## Add a Comment

After confirmation only, run:

- `uvx jira2cli comment <KEY> <BODY> --json`

## Update a Comment

After confirmation only, run:

- `uvx jira2cli comment-update <KEY> <COMMENT_ID> <BODY> --json`

## Delete a Comment

After confirmation only, run:

- `uvx jira2cli comment-delete <KEY> <COMMENT_ID> --json`

Use `--raw` instead of `--json` only when you need API-oriented output. `--raw` renders API-oriented output by parsing JSON when needed, then pretty-printing it with recursively sorted object keys; it does not emit untouched HTTP bytes.

## Mentions

Comment add and update bodies recognize canonical `[~accountId:<id>]` as one semantic ADF mention; Jira may notify that account. Escaped, malformed, code, link, and image forms remain text. Formatted comment Markdown is presentation-only and can lose mention identity when written back, so preserve raw ADF from `comments --json` for identity-safe updates.

Do not post, overwrite, or delete a comment before checking the current issue and recent comments.
