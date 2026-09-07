# Attachment Management

Use this when the issue context already identifies the Jira issue key or attachment ID and you need to inspect, download, upload, or delete attachments.

## Workflow

1. Read the issue first so the target is explicit:
   - `uvx jira2cli read <KEY> --fields summary --json`
2. List attachments on the issue when you need IDs or file names:
   - `uvx jira2cli attachment-list <KEY> --json`
3. Read attachment metadata when you need details for one attachment:
   - `uvx jira2cli attachment-read <ATTACHMENT_ID> --json`
4. Download the attachment when you need local content:
   - `uvx jira2cli attachment <ATTACHMENT_ID>`
   - `uvx jira2cli attachment-download <ATTACHMENT_ID> --output-path <path> --json`
5. Upload only after the user confirms the exact file path and target issue:
   - `uvx jira2cli attachment-upload <KEY> <PATH> --json`
6. Delete only after the user confirms the exact attachment ID:
   - `uvx jira2cli attachment-delete <ATTACHMENT_ID> --json`

## Notes

- `attachment` remains the simple download command.
- `attachment-download` adds structured/raw-friendly output.
- Confirm the exact destination path before downloading or the exact source path before uploading.
- Do not guess attachment IDs or overwrite/delete unexpected files without confirmation.

## Markdown image workflow

For an image already uploaded to an existing issue, `attachment-upload --json` and `--raw` expose each upload item's existing `content` URL. Use it only with that same issue's high-level Markdown as `![alt](attachment-content-url)`:

```bash
upload="$(uvx jira2cli attachment-upload <KEY> screenshot.png --json)"
url="$(jq -er '.[0].content' <<<"$upload")"

uvx jira2cli edit <KEY> --description "Complete replacement text

![Screenshot]($url)" --json
```

The URL also works in comment add/update bodies and worklog add/update comments. Do not use an attachment-content URL during `create`: create the issue, upload to its returned key, then edit the complete rich-text value. External image URLs remain external.
