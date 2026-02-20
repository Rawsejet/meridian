# Scenario 13: Evening Reflection Prompt Notification

## Phase
Notifications

## User Story
At 8pm, Alice receives a prompt to reflect on her day. The notification includes a summary of what she accomplished and a link to the reflection view.

## Preconditions
- Alice has `evening_reflection_enabled: true`, `evening_reflection_time: 20:00`
- Alice has a daily plan with 5 tasks, 3 completed during the day

## Steps
1. Celery beat triggers the evening reflection check at 8pm Alice's time
2. System composes the reflection prompt:
   - "Time to wrap up, Alice! You completed 3 out of 5 tasks today (60%). Ready to reflect on your day?"
   - Includes a deep link to the reflection modal
3. Push notification and/or email sent
4. Alice taps the notification and opens the reflection view (Scenario 09)

## Satisfaction Criteria
- Reflection prompt includes actual completion stats for the day
- If the user already submitted a reflection today, don't send the prompt
- If the user has no plan for today, send a lighter message: "No plan today — want to jot down what you did?"
- The notification deep link opens the reflection modal directly

## Failure Modes
- Reflection already submitted → no duplicate prompt
- User disabled evening reflection → skip entirely

## Satisfaction Score Rubric
- **1.0**: Stats-rich prompt, idempotent (no duplicate if reflected already), deep link works
- **0.8**: Prompt sends with stats but sends even if reflection was already submitted
- **0.5**: Prompt sends but with no completion stats (generic message)
- **0.2**: Celery task exists but doesn't send
- **0.0**: No evening reflection prompt
