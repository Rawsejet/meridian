# Scenario 08: Reordering Tasks Mid-Day

## Phase
Planning

## User Story
Alice started her day with a plan, but a priority changed at 11am. She drags a task from position 5 to position 1 and the plan updates instantly.

## Preconditions
- Alice has a plan for today with 5 tasks in order: [A, B, C, D, E]
- Task B is already marked as completed

## Steps
1. Alice's dashboard shows her plan with B marked complete and grayed out
2. An urgent task E needs to be done next — Alice drags E from position 5 to position 1
3. Frontend sends `PATCH /plans/2025-01-15/reorder` with `{"task_order": [E, A, C, D, B]}`
4. Server validates and updates the order
5. Frontend shows the new order with optimistic update (instant visual feedback)
6. The completed task B remains marked as completed in its new position
7. Alice later drags A below D: `{"task_order": [E, C, D, A, B]}`

## Satisfaction Criteria
- Reorder is a PATCH, not a full plan replacement (idempotent, safe to retry)
- The reorder preserves completion state — completed tasks stay completed
- Optimistic update: frontend shows new order before server confirms
- If server rejects the reorder, frontend rolls back to the previous order
- Reorder with the same task set in a different order succeeds
- Reorder with a different task set (adding/removing tasks) is rejected (use POST to update the full plan)

## Failure Modes
- Reorder with a task not in the original plan returns 422 with `PLAN_TASK_SET_MISMATCH`
- Reorder with missing tasks (fewer than original) returns 422 with `PLAN_TASK_SET_MISMATCH`
- Rapid consecutive reorders (drag-drag-drag) don't corrupt the plan (last write wins, or queue requests)

## Satisfaction Score Rubric
- **1.0**: Reorder works with optimistic updates, rollback on failure, completion state preserved
- **0.8**: Reorder works but no optimistic update (waits for server)
- **0.5**: Reorder works via API but frontend drag-and-drop doesn't trigger it
- **0.2**: Reorder endpoint exists but doesn't validate task set consistency
- **0.0**: No reorder capability
