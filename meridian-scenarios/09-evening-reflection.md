# Scenario 09: Evening Reflection and Day Completion

## Phase
Planning

## User Story
At 8pm, Alice reviews her day. She marks which tasks she completed, logs how long each actually took, notes why she skipped one, rates her mood, and saves the reflection.

## Preconditions
- Alice has a plan for today with 5 tasks: [A, B, C, D, E]
- Task B was already marked in-progress during the day

## Steps
1. Alice opens the evening reflection modal (triggered by notification or manually)
2. Frontend shows the 5 planned tasks with checkboxes
3. Alice marks A as completed, actual time: 90 minutes (estimated was 120)
4. Alice marks B as completed, actual time: 30 minutes (estimated was 45)
5. Alice marks C as completed, actual time: 60 minutes (no estimate was set)
6. Alice leaves D unchecked — she'll do it tomorrow
7. Alice marks E as skipped with reason: "Meeting ran long, rescheduled to Friday"
8. Alice sets her mood to 4 (out of 5) and adds a note: "Productive day despite the meeting overrun"
9. Alice submits: `POST /plans/2025-01-15/complete` with completion data
10. Server creates `task_completion` records for all 5 tasks
11. Server updates the daily_plan with `mood: 4` and notes
12. Server marks tasks A, B, C as `status: completed` with `completed_at` timestamps
13. Task D remains `pending` for tomorrow
14. Task E remains `pending` but has a skip record

## Satisfaction Criteria
- Every task in the plan gets a `task_completion` record (completed or not)
- `task_completion.planned_position` matches the task's position in `task_order`
- `actual_minutes` is recorded for completed tasks, NULL for skipped/incomplete
- Completed tasks have `actual_completed: true`, skipped/incomplete have `false`
- The `skipped_reason` field captures why a task was skipped
- Daily plan `mood` is an integer 1-5
- The reflection can be submitted partially and updated later (PATCH semantics)
- `GET /plans/2025-01-15/reflection` returns computed stats: 3/5 completed (60%), total estimated vs actual time, average mood trend

## Failure Modes
- Submitting completion for a date with no plan returns 404
- Submitting a mood of 0 or 6 returns 422
- Submitting actual_minutes as negative returns 422
- Submitting completion twice merges with existing data (doesn't create duplicates)

## Satisfaction Score Rubric
- **1.0**: Full reflection flow with mood, notes, skip reasons, stats computation, idempotent submission
- **0.8**: Reflection works but stats endpoint is missing or incomplete
- **0.5**: Can mark tasks complete but no mood/notes/skip reasons
- **0.2**: Completion endpoint exists but doesn't create proper task_completion records
- **0.0**: No completion/reflection capability
