# Scenario 07: Creating a Daily Plan with Drag-and-Drop Ordering

## Phase
Planning

## User Story
Alice starts her day by opening Meridian and creating her daily plan. She sees her pending tasks, drags them into her preferred order for the day, and saves the plan.

## Preconditions
- Alice has 8 pending tasks with varying priorities and categories
- No plan exists for today

## Steps
1. Alice navigates to the daily planning view for today
2. Frontend calls `GET /plans/2025-01-15` → returns 404 (no plan yet)
3. Frontend shows Alice's pending tasks sorted by priority (highest first)
4. Alice drags "Write quarterly report" (priority 3) to position 1
5. Alice drags "Team standup" (priority 2) to position 2
6. Alice drags "Buy birthday gift" (priority 2) to position 3
7. Alice selects 5 of her 8 tasks for today (leaving 3 for later)
8. Alice saves the plan: `POST /plans/2025-01-15` with `{"task_order": [uuid1, uuid2, uuid3, uuid4, uuid5]}`
9. Server creates the daily_plan record with the ordered task array
10. Server returns the plan with full task details in order

## Satisfaction Criteria
- The `task_order` array preserves exact ordering (position matters)
- All task IDs in the order must belong to the authenticated user
- All task IDs must reference non-cancelled tasks
- Duplicate task IDs in the order are rejected (422)
- A plan for a given date is unique per user (creating a second plan for the same date updates the existing one via upsert)
- The response includes full task objects (not just IDs) for frontend display
- Frontend drag-and-drop produces smooth visual feedback (no jitter or flashing)

## Failure Modes
- Submitting a plan with a task ID belonging to another user returns 422 with `PLAN_INVALID_TASK`
- Submitting a plan with a cancelled task ID returns 422 with `PLAN_CANCELLED_TASK`
- Submitting an empty task_order returns 422 (at least 1 task required)
- Creating a plan for a date more than 7 days in the future returns 422 with `PLAN_DATE_TOO_FAR`

## Satisfaction Score Rubric
- **1.0**: Plan creation works, drag-and-drop is smooth, validation catches all edge cases, upsert behavior correct
- **0.8**: Plan creation works but drag-and-drop has minor visual issues
- **0.5**: Plan can be created via API but drag-and-drop doesn't work in frontend
- **0.2**: Endpoint exists but validation is missing (accepts invalid task IDs)
- **0.0**: No planning endpoint
