# Scenario 06: Task Search and Cursor-Based Pagination

## Phase
Tasks

## User Story
Alice has accumulated 50+ tasks over several weeks. She searches for a specific task by keyword, and browses her task list page by page using cursor-based pagination.

## Preconditions
- Alice has 55 tasks with varied titles, categories, priorities, and dates

## Steps
1. Alice requests `GET /tasks?limit=20` → receives 20 tasks and a `next_cursor` token
2. Alice requests `GET /tasks?limit=20&cursor={next_cursor}` → receives next 20 tasks and another cursor
3. Alice requests again with new cursor → receives 15 tasks and no `next_cursor` (end of list)
4. Alice searches: `GET /tasks?search=report` → receives all tasks with "report" in the title (case-insensitive)
5. Alice combines search and filter: `GET /tasks?search=report&category=work` → narrower results
6. Alice filters by date range: `GET /tasks?due_after=2025-01-15&due_before=2025-01-31` → only tasks due in that window

## Satisfaction Criteria
- Cursor-based pagination (not offset-based) — cursors are opaque tokens, not page numbers
- Default page size is 20, configurable up to 100
- Cursors are stable: inserting a new task doesn't cause duplicates or skips in existing pagination
- Search is case-insensitive and searches `title` field (optionally `description` too)
- Response format includes: `{"tasks": [...], "next_cursor": "..." | null, "has_more": true|false}`
- Empty result set returns `{"tasks": [], "next_cursor": null, "has_more": false}` (not 404)

## Failure Modes
- Using an invalid cursor returns 400 with `TASK_INVALID_CURSOR`
- Requesting `limit=0` or `limit=-1` returns 422
- Requesting `limit=500` returns 422 (exceeds max)

## Satisfaction Score Rubric
- **1.0**: Cursor pagination + search + combined filters + stable cursors + proper response format
- **0.8**: Pagination works but uses offset instead of cursor
- **0.5**: Pagination works but search is missing or case-sensitive
- **0.2**: List endpoint exists but no pagination (returns all results)
- **0.0**: List endpoint broken or missing
