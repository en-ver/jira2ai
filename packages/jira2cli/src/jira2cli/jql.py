"""Shared JQL syntax reference text for jira2cli."""

JQL_REFERENCE = """\
# JQL (Jira Query Language) Syntax Reference

## Fields

| Field | Description | Example |
|-------|-------------|---------|
| project | Project key | `project = PROJ` |
| status | Issue status | `status = "In Progress"` |
| statusCategory | Status category | `statusCategory = "To Do"` |
| assignee | Assigned user | `assignee = currentUser()` |
| reporter | Issue creator | `reporter = currentUser()` |
| creator | Issue creator (alias) | `creator = currentUser()` |
| issuetype | Issue type | `issuetype = Bug` |
| priority | Issue priority | `priority = "P1 - Critical"` |
| labels | Issue labels | `labels = backend` |
| component | Component | `component = "Frontend"` |
| fixVersion | Fix version | `fixVersion = "2025-Q1"` |
| sprint | Sprint | `sprint in openSprints()` |
| parent | Parent issue | `parent = PROJ-100` |
| summary | Issue title | `summary ~ "login"` |
| description | Issue description | `description ~ "error"` |
| comment | Comment text | `comment ~ "reviewed"` |
| text | All text fields | `text ~ "search term"` |
| created | Creation date | `created >= -7d` |
| updated | Last update date | `updated >= "2025-01-01"` |
| resolved | Resolution date | `resolved >= startOfMonth()` |
| due | Due date | `due <= endOfWeek()` |
| resolution | Resolution type | `resolution = Unresolved` |

## Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `status = Open` |
| `!=` | Not equals | `status != Closed` |
| `>` | Greater than | `created > "2025-01-01"` |
| `>=` | Greater or equal | `priority >= "P2 - Major"` |
| `<` | Less than | `due < now()` |
| `<=` | Less or equal | `updated <= -30d` |
| `~` | Contains (text) | `summary ~ "login bug"` |
| `!~` | Not contains | `summary !~ "test"` |
| `IN` | In list | `status IN ("Open", "In Progress")` |
| `NOT IN` | Not in list | `priority NOT IN ("P4 - Trivial")` |
| `IS` | Is empty/null | `assignee IS EMPTY` |
| `IS NOT` | Is not empty | `assignee IS NOT EMPTY` |
| `WAS` | Was previously | `status WAS "In Progress"` |
| `WAS IN` | Was in list | `status WAS IN ("Open", "Reopened")` |
| `WAS NOT` | Was not previously | `status WAS NOT "Closed"` |
| `CHANGED` | Field was changed | `status CHANGED` |

## Keywords

- `AND` — combine conditions: `project = PROJ AND status = Open`
- `OR` — either condition: `assignee = currentUser() OR reporter = currentUser()`
- `NOT` — negate: `NOT status = Closed`
- `ORDER BY` — sort results: `ORDER BY created DESC`
- `EMPTY` / `NULL` — no value: `assignee IS EMPTY`

## Functions

| Function | Description | Example |
|----------|-------------|---------|
| `currentUser()` | Logged-in user | `assignee = currentUser()` |
| `membersOf("group")` | Users in a group | `assignee IN membersOf("developers")` |
| `now()` | Current date/time | `due < now()` |
| `startOfDay()` | Start of today | `created >= startOfDay()` |
| `endOfDay()` | End of today | `due <= endOfDay()` |
| `startOfWeek()` | Start of this week | `created >= startOfWeek()` |
| `endOfWeek()` | End of this week | `due <= endOfWeek()` |
| `startOfMonth()` | Start of this month | `created >= startOfMonth()` |
| `endOfMonth()` | End of this month | `due <= endOfMonth()` |
| `startOfYear()` | Start of this year | `created >= startOfYear()` |
| `endOfYear()` | End of this year | `due <= endOfYear()` |
| `openSprints()` | Currently active sprints | `sprint IN openSprints()` |
| `closedSprints()` | Completed sprints | `sprint IN closedSprints()` |
| `futureSprints()` | Upcoming sprints | `sprint IN futureSprints()` |

Time functions accept offsets: `startOfDay(-1)` = yesterday, `startOfMonth(-2)` = two months ago.

## Relative Dates

Use with date fields (`created`, `updated`, `due`, `resolved`):
- `-1d` — 1 day ago
- `-7d` — 7 days ago
- `-1w` — 1 week ago
- `-1M` — 1 month ago (uppercase M)
- `-1y` — 1 year ago

Example: `updated >= -7d` — updated in the last 7 days.

## CHANGED Keyword

Find issues where a field value was changed. Supports these predicates:

| Predicate | Description | Example |
|-----------|-------------|---------|
| `BY` | Changed by user | `status CHANGED BY currentUser()` |
| `FROM` | Changed from value | `status CHANGED FROM "Open"` |
| `TO` | Changed to value | `status CHANGED TO "Closed"` |
| `DURING` | Changed in date range | `status CHANGED DURING ("2025-01-01", "2025-06-01")` |
| `AFTER` | Changed after date | `status CHANGED AFTER "2025-01-01"` |
| `BEFORE` | Changed before date | `status CHANGED BEFORE "2025-06-01"` |

Predicates can be combined:
`status CHANGED BY currentUser() FROM "In Progress" TO "Done" AFTER "2025-01-01"`

Fields that support CHANGED: `status`, `assignee`, `reporter`, `priority`, `issuetype`, `resolution`, `summary`, `description`, `fixVersion`, `component`, `labels`, `sprint`.

**Note:** CHANGED tracks field-level changes only. It does not cover comments, attachments, or link changes. To find issues you commented on, use `comment ~ currentUser()` (searches comment text, not author) or combine multiple conditions.

## Common Query Patterns

```
# Issues assigned to me
assignee = currentUser()

# My open issues
assignee = currentUser() AND resolution = Unresolved

# Issues I created
reporter = currentUser()

# Issues where I changed the status
status CHANGED BY currentUser()

# Issues where any tracked field was changed by me
assignee CHANGED BY currentUser() OR status CHANGED BY currentUser() \
  OR priority CHANGED BY currentUser()

# Recently updated issues in a project
project = PROJ AND updated >= -7d ORDER BY updated DESC

# Overdue issues
due < now() AND resolution = Unresolved

# Unassigned bugs
issuetype = Bug AND assignee IS EMPTY

# High priority open issues
priority IN ("P0 - Blocker", "P1 - Critical") AND resolution = Unresolved

# Issues created this month
created >= startOfMonth() ORDER BY created DESC

# Text search across all fields
text ~ "search term"

# Issues with a specific label
labels = "backend" AND project = PROJ

# Issues in current sprint
sprint IN openSprints() AND project = PROJ

# Issues resolved last week
resolved >= startOfWeek(-1) AND resolved < startOfWeek()
```
"""

__all__ = ["JQL_REFERENCE"]
