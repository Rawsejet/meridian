# Scenario 11: Morning Briefing Notification

## Phase
Notifications

## User Story
At 8am local time, Alice receives a morning briefing — either as a web push notification or an email — summarizing today's planned tasks and highlighting the most urgent ones.

## Preconditions
- Alice has `morning_briefing_enabled: true`, `morning_briefing_time: 08:00`
- Alice's timezone is `America/Los_Angeles`
- Alice has a daily plan for today with 5 tasks
- Alice has a web push subscription registered

## Steps
1. Celery beat fires the morning briefing check job at regular intervals (every minute or every 5 minutes)
2. The job queries users whose `morning_briefing_time` matches the current time in their timezone (±5 min window)
3. Alice is in the result set
4. A Celery task is enqueued: `send_morning_briefing(user_id=alice_id)`
5. The task fetches Alice's plan for today
6. The task composes the briefing content:
   - "Good morning, Alice! You have 5 tasks planned today."
   - Lists top 3 by priority with estimated times
   - Total estimated time: 4h 15m
   - "Your most urgent: Write quarterly report (due today)"
7. The task sends a web push notification via pywebpush
8. The task also sends an email via SMTP (if email_notifications enabled)
9. The notification is logged for audit

## Satisfaction Criteria
- The briefing fires at the user's local time, not server time
- Users in different timezones receive their briefing at their configured local time
- The briefing includes: task count, top tasks by priority, total estimated time, any tasks due today
- If the user has no plan for today, the briefing says "No tasks planned — want to set up your day?"
- Push notification payload includes a deep link to the daily plan view
- Email contains the same content in HTML format
- The job is idempotent: if it runs twice for the same user on the same day, only one notification is sent
- Quiet hours are respected: if morning_briefing_time falls within quiet_hours, the notification is delayed to quiet_hours_end

## Failure Modes
- Push subscription expired → log the error, remove the subscription, deliver via email only
- SMTP server unreachable → retry 3 times with exponential backoff, then mark as failed
- User disabled morning briefing → skip entirely (no error)
- User has no plan and no tasks → send a lighter "All clear today!" message

## Satisfaction Score Rubric
- **1.0**: Timezone-correct delivery, rich content, push + email, idempotent, quiet hours respected, subscription cleanup
- **0.8**: Delivery works but quiet hours not implemented or no deep link in push
- **0.5**: Notification sends but at wrong time (UTC instead of local) or content is bare
- **0.2**: Celery task exists but doesn't actually send notifications
- **0.0**: No morning briefing implementation
