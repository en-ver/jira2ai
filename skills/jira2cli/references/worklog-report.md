# Worklog Report

Use this when you need a worklog report for issues selected by JQL within a UTC date range.

## Workflow

1. If the JQL is new or uncertain, validate it first:
   - `uv run jira2cli jql-syntax`
   - `uv run jira2cli search '<JQL>' --field key --field summary --max-results <N> --json`
2. Run the report:
   - `uv run jira2cli worklog-report --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --jql '<JQL>' --json`
3. Use `--account-id <ACCOUNT_ID>` when the report should include worklogs from only one Jira user.
4. Use `--max-issues <N>` when you need a smaller or larger scan limit than the default `100`.
5. Add `--include-details` when you need optional detail fields such as `updateAuthor`, `visibility`, `comment`, or `properties`.
6. Use `--raw` instead of `--json` when you need the untouched API payload.

## Notes

- Issue selection is JQL-only. For a single issue, use `--jql 'issue = PROJ-123'`.
- Dates are interpreted in UTC, and `--end-date` is inclusive.
- `--account-id` filters returned worklogs client-side by author `accountId`.
- `--max-issues` must be at least `1`; if more issues match than the limit, the report notes truncation.
- Output rows use `displayName` as the friendly user name.
- Results still depend on the configured Jira account's issue and worklog visibility.
