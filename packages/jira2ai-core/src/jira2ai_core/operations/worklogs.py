"""Worklog report operations."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta

from jira2py import JiraAPI

from ..errors import Jira2AIValidationError, JiraOperationError
from ..formatters import format_worklog_report
from ..models import (
    JiraIssue,
    JiraWorklog,
    SearchResult,
    WorklogIssueSelector,
    WorklogPage,
    WorklogReport,
    WorklogReportRow,
)
from ..results import OperationResult

_WORKLOG_FIELDS = ["summary", "project"]
_SEARCH_PAGE_SIZE = 5_000
_WORKLOG_PAGE_SIZE = 5_000
_STRICT_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def get_worklog_report(
    api: JiraAPI,
    *,
    start_date: str,
    end_date: str,
    jql: str,
    account_id: str | None = None,
    max_issues: int = 100,
    include_details: bool = False,
) -> OperationResult:
    """Build a worklog report for issues selected by JQL."""
    if not jql.strip():
        raise Jira2AIValidationError("jql must not be empty.")
    if max_issues < 1:
        raise Jira2AIValidationError("max_issues must be at least 1.")

    start_dt, exclusive_end_dt = _validate_date_range(
        start_date=start_date,
        end_date=end_date,
    )
    issues, selector = _search_report_issues(api=api, jql=jql, max_issues=max_issues)

    rows: list[WorklogReportRow] = []
    for issue in issues:
        rows.extend(
            _collect_issue_rows(
                api=api,
                issue=issue,
                start_dt=start_dt,
                exclusive_end_dt=exclusive_end_dt,
                account_id=account_id,
                include_details=include_details,
            )
        )

    rows.sort(key=lambda row: (row.dateTime, row.issueKey, row.worklogId or ""))
    total_seconds = sum(row.timeSpentSeconds or 0 for row in rows)
    report = WorklogReport(
        startDate=start_date,
        endDate=end_date,
        timezone="UTC",
        endDateInclusive=True,
        startedAtOrAfter=_format_utc(start_dt),
        startedBefore=_format_utc(exclusive_end_dt),
        accountId=account_id,
        issueSelector=selector,
        rowCount=len(rows),
        totalSeconds=total_seconds,
        totalHours=_seconds_to_hours(total_seconds),
        rows=rows,
    )
    data = report.model_dump(mode="json")
    return OperationResult.with_data(format_worklog_report(report), data)


def _search_report_issues(
    *,
    api: JiraAPI,
    jql: str,
    max_issues: int,
) -> tuple[list[JiraIssue], WorklogIssueSelector]:
    issues: list[JiraIssue] = []
    next_page_token: str | None = None
    total: int | None = None

    while len(issues) < max_issues:
        remaining = max_issues - len(issues)
        try:
            data = api.search.enhanced_search(
                jql=jql,
                next_page_token=next_page_token,
                max_results=min(remaining, _SEARCH_PAGE_SIZE),
                fields=_WORKLOG_FIELDS,
            )
        except Exception as exc:
            raise JiraOperationError(
                f"Failed to search issues for worklog report: {exc}"
            ) from exc

        result = SearchResult.model_validate(data)
        total = result.total if result.total is not None else total
        if not result.issues:
            next_page_token = result.nextPageToken
            break

        issues.extend(result.issues[:remaining])
        next_page_token = result.nextPageToken
        if not next_page_token:
            break

    selector = WorklogIssueSelector(
        jql=jql,
        maxIssues=max_issues,
        issuesReturned=len(issues),
        truncated=bool(next_page_token) or (total is not None and len(issues) < total),
        nextPageToken=next_page_token,
        total=total,
    )
    return issues, selector


def _collect_issue_rows(
    *,
    api: JiraAPI,
    issue: JiraIssue,
    start_dt: datetime,
    exclusive_end_dt: datetime,
    account_id: str | None,
    include_details: bool,
) -> list[WorklogReportRow]:
    rows: list[WorklogReportRow] = []
    start_at = 0
    issue_identifier = issue.id or issue.key
    started_after = _to_started_after_millis(start_dt)
    started_before = _to_epoch_millis(exclusive_end_dt)

    while True:
        try:
            data = api.worklogs.get_worklogs(
                issue_id=issue_identifier,
                start_at=start_at,
                max_results=_WORKLOG_PAGE_SIZE,
                extra_params={
                    "startedAfter": started_after,
                    "startedBefore": started_before,
                },
            )
        except Exception as exc:
            raise JiraOperationError(
                f"Failed to fetch worklogs for {issue.key}: {exc}"
            ) from exc

        page = WorklogPage.model_validate(data)
        if not page.worklogs:
            break

        for worklog in page.worklogs:
            row = _build_row(
                issue=issue,
                worklog=worklog,
                start_dt=start_dt,
                exclusive_end_dt=exclusive_end_dt,
                account_id=account_id,
                include_details=include_details,
            )
            if row is not None:
                rows.append(row)

        start_at = page.startAt + len(page.worklogs)
        if start_at >= page.total:
            break

    return rows


def _build_row(
    *,
    issue: JiraIssue,
    worklog: JiraWorklog,
    start_dt: datetime,
    exclusive_end_dt: datetime,
    account_id: str | None,
    include_details: bool,
) -> WorklogReportRow | None:
    started_dt = _parse_jira_datetime(worklog.started)
    if started_dt is None or not (start_dt <= started_dt < exclusive_end_dt):
        return None

    author = worklog.author
    author_account_id = author.accountId if author else ""
    if account_id is not None and author_account_id != account_id:
        return None

    return WorklogReportRow(
        dateTime=_format_utc(started_dt),
        issueId=issue.id or worklog.issueId,
        issueKey=issue.key,
        accountId=author_account_id,
        displayName=author.displayName if author else "Unknown",
        timeSpentHours=_seconds_to_hours(worklog.timeSpentSeconds),
        worklogId=worklog.id or None,
        issueSummary=issue.fields.summary,
        projectKey=issue.fields.project.key if issue.fields.project else None,
        started=_format_optional_utc(worklog.started),
        created=_format_optional_utc(worklog.created),
        updated=_format_optional_utc(worklog.updated),
        timeSpentSeconds=worklog.timeSpentSeconds,
        timeSpent=worklog.timeSpent,
        updateAuthor=worklog.updateAuthor if include_details else None,
        visibility=worklog.visibility if include_details else None,
        comment=worklog.comment if include_details else None,
        properties=worklog.properties if include_details else None,
    )


def _validate_date_range(
    *, start_date: str, end_date: str
) -> tuple[datetime, datetime]:
    start_day = _parse_date(start_date, field_name="start_date")
    end_day = _parse_date(end_date, field_name="end_date")
    if end_day < start_day:
        raise Jira2AIValidationError("end_date must be on or after start_date.")

    start_dt = datetime.combine(start_day, time.min, tzinfo=UTC)
    exclusive_end_dt = datetime.combine(
        end_day + timedelta(days=1), time.min, tzinfo=UTC
    )
    return start_dt, exclusive_end_dt


def _parse_date(value: str, *, field_name: str) -> date:
    if _STRICT_DATE_RE.fullmatch(value) is None:
        raise Jira2AIValidationError(f"{field_name} must be in YYYY-MM-DD format.")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Jira2AIValidationError(
            f"{field_name} must be in YYYY-MM-DD format."
        ) from exc


def _parse_jira_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    elif (
        len(normalized) >= 5 and normalized[-5] in {"+", "-"} and normalized[-3] != ":"
    ):
        normalized = normalized[:-2] + ":" + normalized[-2:]

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_optional_utc(value: str | None) -> str | None:
    parsed = _parse_jira_datetime(value)
    return _format_utc(parsed) if parsed else value


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _seconds_to_hours(seconds: int) -> float:
    return round(seconds / 3600, 2)


def _to_epoch_millis(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _to_started_after_millis(value: datetime) -> int:
    epoch_millis = _to_epoch_millis(value)
    return epoch_millis - 1 if epoch_millis > 0 else 0


__all__ = ["get_worklog_report"]
