# Scenario 12: Midday Smart Nudge

## Phase
Notifications

## User Story
At noon, Meridian checks Alice's progress. She's only completed 1 of her 5 planned tasks. Meridian sends a gentle nudge with the remaining tasks prioritized.

## Preconditions
- Alice has `midday_nudge_enabled: true`, `midday_nudge_time: 12:00`
- Alice has a daily plan with 5 tasks
- 1 task is marked completed (via the complete task endpoint)
- Current time is noon in Alice's timezone

## Steps
1. Celery beat triggers the midday nudge check
2. System finds Alice is eligible (noon in her timezone, nudge enabled)
3. System checks Alice's plan completion: 1/5 tasks done (20%)
4. Since <50% completion, a nudge is warranted
5. Nudge content: "Hey Alice, you've knocked out 1 task so far! 4 to go. Next up: [highest priority remaining task]. You've got this!"
6. Nudge is sent via web push and/or email

## Steps — No Nudge Needed
1. Same setup, but Alice has completed 3/5 tasks (60%)
2. Since ≥50% completion, no nudge is sent
3. Nothing happens — no notification

## Steps — Customized Threshold
1. A future version might let users set their own nudge threshold
2. For now, the 50% threshold is hardcoded but extracted to a config constant

## Satisfaction Criteria
- Nudge only fires if completion rate is below 50%
- Nudge includes the count of remaining tasks and the next highest-priority one
- If all tasks are done, no nudge is sent (even if it's noon)
- If there's no plan for today, no nudge is sent
- The nudge tone is encouraging, not guilt-inducing
- The 50% threshold is a named constant, not a magic number
- Nudge is idempotent per user per day

## Failure Modes
- User completes a task between the check and the send → stale data is acceptable (eventual consistency)
- User has a plan but all tasks are cancelled → no nudge (0 actionable tasks)

## Satisfaction Score Rubric
- **1.0**: Smart nudge with completion check, encouraging tone, idempotent, threshold as constant
- **0.8**: Nudge fires correctly but always sends regardless of completion rate
- **0.5**: Nudge fires but content is generic (no task details)
- **0.2**: Celery task scheduled but no completion check logic
- **0.0**: No midday nudge implementation
