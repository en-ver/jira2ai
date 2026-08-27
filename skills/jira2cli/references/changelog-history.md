# Changelog History

Use these read-only commands for the change history of one known Jira issue.

## Discover complete history

```bash
uvx jira2cli changelogs <KEY> --json
uvx jira2cli changelogs <KEY> \
  --created-at-or-after <ISO-8601> \
  --created-before <ISO-8601> --json
```

`changelogs` follows every Jira GET page before returning a complete helper-owned envelope:

```json
{"issue_key":"<KEY>","changelogs":[...]}
```

Timestamp filters are **client-side**, not Jira request filters. They use the half-open interval `created_at_or_after <= created < created_before`, so the lower bound is inclusive and the upper bound is exclusive. All pages are still fetched before filtering.

## Retrieve known IDs

After inspecting history, retrieve exact IDs with one required plural CSV option:

```bash
uvx jira2cli changelogs-by-ids <KEY> --changelog-ids 10001,10002 --json
```

This is distinct from discovery: it uses Jira's known-ID POST endpoint. Do not use it as a paginated-history substitute. IDs are comma-separated base-10 integers in exactly one `--changelog-ids` occurrence; whitespace is trimmed, empty segments are rejected, and order and duplicates are forwarded. Jira controls the response order, so do not assume it matches the requested ID order.

Normal output is condensed text. `--json` and `--raw` both render the same normalized helper-owned structured envelope, not untouched HTTP output. Complete histories and structured results can be large; the CLI does not cap them, but a terminal or external harness may clip them.
