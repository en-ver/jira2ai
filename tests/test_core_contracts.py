import subprocess
import sys

from jira2ai_core.errors import (
    AttachmentDownloadError,
    AttachmentPathError,
    Jira2AIConfigError,
    Jira2AIValidationError,
    JiraOperationError,
)
from jira2ai_core.models import FieldMeta, FieldSchema
from jira2ai_core.results import OperationResult


def test_operation_result_supports_text_only_and_raw_payloads() -> None:
    text_only = OperationResult.text_only("hello")
    assert text_only.text == "hello"
    assert text_only.data is None
    assert text_only.raw_content is None
    assert text_only.has_raw_output is False

    with_data = OperationResult.with_data(
        "done",
        {"key": "PROJ-123"},
        raw_content='{"key":"PROJ-123"}',
    )
    assert with_data.text == "done"
    assert with_data.data == {"key": "PROJ-123"}
    assert with_data.raw_content == '{"key":"PROJ-123"}'
    assert with_data.has_raw_output is True


def test_core_errors_keep_message_and_details() -> None:
    error = JiraOperationError(
        "Failed to update issue PROJ-123",
        details={"issue_key": "PROJ-123", "operation": "edit"},
    )

    assert str(error) == "Failed to update issue PROJ-123"
    assert error.details == {"issue_key": "PROJ-123", "operation": "edit"}


def test_core_error_hierarchy_covers_expected_contracts() -> None:
    assert isinstance(Jira2AIValidationError("bad input"), Exception)
    assert isinstance(Jira2AIConfigError("missing token"), Exception)
    assert isinstance(AttachmentPathError("outside roots"), Exception)
    assert isinstance(AttachmentDownloadError("download failed"), Exception)


def test_field_meta_parses_jira_schema_and_dumps_renamed_field() -> None:
    field = FieldMeta.model_validate(
        {
            "fieldId": "summary",
            "name": "Summary",
            "schema": {"type": "string"},
        }
    )

    assert field.jira_schema == FieldSchema(type="string")
    assert "jira_schema" in FieldMeta.model_fields
    assert "schema" not in FieldMeta.model_fields

    dumped = field.model_dump()
    assert dumped["jira_schema"] == {"type": "string", "custom": ""}
    assert "schema" not in dumped


def test_field_meta_accepts_python_construction_by_jira_schema_name() -> None:
    field = FieldMeta.model_validate(
        {
            "fieldId": "summary",
            "name": "Summary",
            "jira_schema": {"type": "string"},
        }
    )

    assert field.jira_schema == FieldSchema(type="string")


def test_importing_models_with_warning_errors_enabled_succeeds() -> None:
    subprocess.run(
        [
            sys.executable,
            "-W",
            "error::UserWarning",
            "-c",
            "import jira2ai_core.models",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
