"""ADF (Atlassian Document Format) conversion utilities.

Uses pyadf for ADF→Markdown (reading from Jira)
and marklassian for Markdown→ADF (writing to Jira).
"""

import logging
from typing import Any

from marklassian import AdfDocument, AdfNode
from marklassian import markdown_to_adf as _markdown_to_adf
from pyadf import Document

logger = logging.getLogger(__name__)


def adf_to_markdown(adf: Any) -> str:
    """Convert ADF JSON to Markdown.

    Args:
        adf: ADF document as a dictionary, or None.

    Returns:
        Markdown string, or "(none)" if input is empty/invalid.
    """
    if not adf or not isinstance(adf, dict):
        return "(none)"

    try:
        doc = Document(adf)
        md = doc.to_markdown()
        return md.strip() if md else "(none)"
    except Exception:
        logger.exception("ADF to Markdown conversion failed, using plain text fallback")
        return _extract_text_fallback(adf)


def markdown_to_adf(markdown: str) -> AdfDocument:
    """Convert Markdown to ADF JSON.

    Args:
        markdown: Markdown string.

    Returns:
        ADF document as a TypedDict.
    """
    if not markdown or not markdown.strip():
        return AdfDocument(type="doc", version=1, content=[])

    try:
        return _markdown_to_adf(markdown)
    except Exception:
        logger.exception("Markdown to ADF conversion failed, wrapping as plain text")
        return AdfDocument(
            type="doc",
            version=1,
            content=[
                AdfNode(
                    type="paragraph",
                    content=[AdfNode(type="text", text=markdown)],
                )
            ],
        )


# --- ADF field detection ---

# System fields known to use ADF format
_ADF_SYSTEM_FIELDS: set[str] = {"description", "environment"}

# Custom field schema suffix indicating ADF (rich-text paragraph)
_ADF_CUSTOM_SUFFIX = ":textarea"


def is_adf_value(value: Any) -> bool:
    """Check if a value looks like an ADF document.

    ADF documents are dicts with ``{"type": "doc", "version": 1, "content": [...]}``.
    """
    return isinstance(value, dict) and value.get("type") == "doc"


def is_adf_field(field_id: str, custom_schema: str = "") -> bool:
    """Check if a field is known to use ADF format.

    Detection is based on:
    - Known system fields (description, environment)
    - Custom field schema containing ':textarea'
    """
    if field_id in _ADF_SYSTEM_FIELDS:
        return True
    if custom_schema and _ADF_CUSTOM_SUFFIX in custom_schema:
        return True
    return False


def convert_adf_values(data: dict[str, Any]) -> dict[str, Any]:
    """Convert any ADF values in a dict to markdown strings.

    Iterates over all values and converts those that look like ADF documents.
    Non-ADF values are left unchanged.
    """
    result = {}
    for key, value in data.items():
        if is_adf_value(value):
            result[key] = adf_to_markdown(value)
        else:
            result[key] = value
    return result


def detect_adf_field_ids(fields_metadata: list[dict[str, Any]]) -> set[str]:
    """Build a set of field IDs that use ADF format.

    Examines field metadata from the Jira fields API and identifies
    fields that use ADF based on known system fields and custom textarea schema.

    Args:
        fields_metadata: List of field dicts from ``api.fields.get_fields()``.

    Returns:
        Set of field IDs that expect ADF format.
    """
    adf_ids = set(_ADF_SYSTEM_FIELDS)
    for field in fields_metadata:
        field_id = field.get("id", "")
        schema = field.get("schema", {}) or {}
        custom = schema.get("custom", "")
        if custom and _ADF_CUSTOM_SUFFIX in custom:
            adf_ids.add(field_id)
    return adf_ids


def convert_markdown_fields(
    fields: dict[str, Any],
    adf_field_ids: set[str],
) -> dict[str, Any]:
    """Convert markdown string values to ADF for known ADF fields.

    Only converts values that are plain strings and whose field ID
    is in the provided set of ADF field IDs.
    """
    result = {}
    for key, value in fields.items():
        if key in adf_field_ids and isinstance(value, str):
            result[key] = markdown_to_adf(value)
        else:
            result[key] = value
    return result


def _extract_text_fallback(adf: dict[str, Any]) -> str:
    """Extract plain text from ADF as a last resort."""
    texts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and "text" in node:
                texts.append(node["text"])
            for child in node.get("content", []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(adf)
    return " ".join(texts).strip() or "(none)"
