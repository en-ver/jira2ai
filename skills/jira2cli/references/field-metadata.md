# Field Metadata

Use this before issue creation or issue edits whenever required fields, editable fields, or allowed values are not already known.

## Create Metadata

1. If the issue type is not confirmed yet, inspect available issue types for the project:
   - `uv run jira2cli fields --project-key <PROJECT> --json`
2. Fetch scoped create metadata:
   - `uv run jira2cli fields --project-key <PROJECT> --issue-type <TYPE> --json`
3. For each field you may set, inspect:
   - `required`
   - `allowedValues`
   - `schema`
   - `defaultValue`
   - any extra raw Jira properties present in the output
4. When `allowedValues` already includes components, versions, priorities, or option lists, use those exact values instead of guessing.
5. If you need the untouched API payload, rerun with `--raw` instead of `--json`.

## Edit Metadata

1. Read the current issue state first:
   - `uv run jira2cli read <KEY> --json`
2. Fetch edit metadata:
   - `uv run jira2cli fields --issue-key <KEY> --json`
3. Inspect the same metadata keys before deciding which fields can be changed.
4. If the field is not present or the required values are still unclear, stop and ask before editing.

## Mutation Rule

Do not guess missing values. Summarize unresolved required fields, defaults, and allowed choices, then ask the user to confirm before creating or editing the issue.
