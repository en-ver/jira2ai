# Changelog History

Use these read-only commands for the change history of one known Jira issue.

## Discover complete history

```bash
uvx jira2cli changelogs <KEY> --json
uvx jira2cli changelogs <KEY> \
  --created-at-or-after <ISO-8601> \
  --created-before <ISO-8601> \
  --field-ids summary,customfield_10001 \
  --result-start-at 0 --result-max-results 20 --json
```

`changelogs` follows every Jira GET page before returning a complete helper-owned envelope:

```json
{"issue_key":"<KEY>","changelogs":[...]}
```

Timestamp filters are **client-side**, not Jira request filters. They use the half-open interval `created_at_or_after <= created < created_before`, so the lower bound is inclusive and the upper bound is exclusive. `--field-ids` is also client-side: it retains only items whose raw `fieldId` exactly matches a canonical field ID, case-sensitively, and drops history events with no retained items. All Jira GET pages are still fetched before filtering.

Without `--result-max-results`, every retained event is returned. Supplying `--result-max-results N` enables local event pagination after complete retrieval and filtering. `--result-start-at` defaults to `0` and may be nonzero only with `--result-max-results`; JSON/raw output then adds helper-owned `result_page` metadata. This is not Jira server pagination.

## Retrieve known IDs

After inspecting history, retrieve exact IDs with one required plural CSV option:

```bash
uvx jira2cli changelogs-by-ids <KEY> \
  --changelog-ids 10001,10002 --field-ids summary --json
```

This is distinct from discovery: it uses Jira's known-ID POST endpoint. Do not use it as a paginated-history substitute. IDs are comma-separated base-10 integers in exactly one `--changelog-ids` occurrence; whitespace is trimmed, empty segments are rejected, and order and duplicates are forwarded. `--field-ids` uses the same exact raw-`fieldId` filtering as `changelogs`. Jira controls the response order, so do not assume it matches the requested ID order. This known-ID operation has no result pagination; batch fewer IDs when a smaller response is needed.

Normal output is condensed text. `--json` and `--raw` both render the same normalized helper-owned structured envelope, not untouched HTTP output. Complete histories and structured results can be large; the CLI applies no implicit result cap. `changelogs --result-max-results` is an explicit local cap, and a terminal or external harness may still clip output.
