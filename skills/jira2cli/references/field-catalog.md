# Field Catalog

Use this read-only command to retrieve one searchable Jira field-catalog page when you need canonical field IDs, names, or system/custom type metadata:

```bash
uvx jira2cli fields-list \
  --project-key <PROJECT> \
  --query <TEXT> \
  --field-ids summary,customfield_10001 \
  --field-types system,custom \
  --start-at 0 --max-results 20 --json
```

All filters are optional. `--field-ids` and `--field-types` are comma-delimited options that may appear at most once. Field types are exactly `system` and/or `custom`. Plain output is concise; `--json` and `--raw` return the complete Jira page envelope, including `values`, `startAt`, `maxResults`, `total`, `isLast`, and other Jira properties.

The command returns exactly one Jira server page. Retain the same filters and continue with `--start-at` equal to returned `startAt + len(values)`; stop when Jira reports `isLast`. Jira can cap the requested size, so use its returned metadata rather than assuming the requested page size.

Jira documents this endpoint for classic projects. `--project-key` supplies only Jira project context/access filtering. It does **not** prove that a field applies to an issue type, Create screen, or Edit screen. Use `fields --project-key <PROJECT> --issue-type <TYPE>` for create metadata and `fields --issue-key <KEY>` for edit metadata before a mutation.
