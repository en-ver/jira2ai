# Attachment Management

Use this when the issue context already identifies the Jira issue key or attachment ID and you need to inspect, download, upload, or delete attachments.

## Workflow

1. Read the issue first so the target is explicit:
   - `uv run jira2cli read <KEY> --json`
2. List attachments on the issue when you need IDs or file names:
   - `uv run jira2cli attachment-list <KEY> --json`
3. Read attachment metadata when you need details for one attachment:
   - `uv run jira2cli attachment-read <ATTACHMENT_ID> --json`
4. Download the attachment when you need local content:
   - `uv run jira2cli attachment <ATTACHMENT_ID>`
   - `uv run jira2cli attachment-download <ATTACHMENT_ID> --output-path <path> --json`
5. Upload only after the user confirms the exact file path and target issue:
   - `uv run jira2cli attachment-upload <KEY> <PATH> --json`
6. Delete only after the user confirms the exact attachment ID:
   - `uv run jira2cli attachment-delete <ATTACHMENT_ID> --json`

## Notes

- `attachment` remains the simple download command.
- `attachment-download` adds structured/raw-friendly output.
- Confirm the exact destination path before downloading or the exact source path before uploading.
- Do not guess attachment IDs or overwrite/delete unexpected files without confirmation.
