# Scenario 04: Create, Read, Update, and Delete Tasks

## Phase
Tasks

## User Story
Alice creates several tasks for her work and personal life, edits one to change the priority, views them filtered by category, and cancels one she no longer needs.

## Preconditions
- Alice is authenticated

## Steps
1. Alice creates task: `{"title": "Write quarterly report", "priority": 3, "category": "work", "estimated_minutes": 120, "energy_level": 3, "due_date": "2025-01-20"}`
2. Server returns the task with a UUID, `status: "pending"`, and `created_at` timestamp
3. Alice creates task: `{"title": "Buy birthday gift for Mom", "priority": 2, "category": "personal", "estimated_minutes": 45, "energy_level": 1}`
4. Alice creates task: `{"title": "Schedule dentist appointment", "priority": 1, "category": "health"}`
5. Alice lists all tasks: `GET /tasks` → returns 3 tasks, newest first
6. Alice filters by category: `GET /tasks?category=work` → returns 1 task
7. Alice filters by priority: `GET /tasks?priority=3` → returns 1 task (the report)
8. Alice updates the birthday gift task: `PATCH /tasks/{id}` with `{"priority": 3, "due_date": "2025-01-18"}` → returns updated task
9. Alice cancels the dentist task: `DELETE /tasks/{id}` → task status becomes "cancelled", not deleted from DB
10. Alice lists tasks: `GET /tasks` → returns 2 tasks (cancelled ones excluded by default)
11. Alice lists all including cancelled: `GET /tasks?include_cancelled=true` → returns 3 tasks

## Satisfaction Criteria
- Task IDs are UUIDs, not sequential integers
- All timestamps are ISO 8601 with timezone (UTC)
- `GET /tasks` returns only the authenticated user's tasks
- Default sort is `created_at DESC`
- Filtering by multiple fields simultaneously works: `GET /tasks?category=work&priority=3`
- Partial update only modifies specified fields, leaving others unchanged
- Delete is soft (sets status to cancelled), not a database row deletion
- Cancelled tasks are excluded from default listing but retrievable with a filter
- `GET /tasks/{id}` for a non-existent or other-user's task returns 404 (not 403, to avoid ID enumeration)

## Failure Modes
- Creating a task with empty title returns 422
- Creating a task with priority 5 (out of range) returns 422
- Creating a task with negative estimated_minutes returns 422
- Updating a non-existent task returns 404
- Patching with an empty object (`{}`) returns the task unchanged (no error)

## Satisfaction Score Rubric
- **1.0**: Full CRUD with filtering, pagination, soft delete, authorization, all edge cases handled
- **0.8**: CRUD works but missing one filter or pagination
- **0.5**: Create and read work but update or soft delete is broken
- **0.2**: Create works but list returns wrong data or ignores auth
- **0.0**: Task endpoints don't exist
