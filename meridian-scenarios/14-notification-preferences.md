# Scenario 14: Notification Preference Management

## Phase
Notifications

## User Story
Alice wants to change her morning briefing to 7am, disable the midday nudge entirely, and set quiet hours from 10pm to 7am.

## Preconditions
- Alice is authenticated with default notification preferences

## Steps
1. Alice views current preferences: `GET /notifications/preferences`
2. Response shows defaults: morning 8am, midday noon, evening 8pm, all enabled, no quiet hours
3. Alice updates: `POST /notifications/preferences` with:
   ```json
   {
     "morning_briefing_time": "07:00",
     "midday_nudge_enabled": false,
     "quiet_hours_start": "22:00",
     "quiet_hours_end": "07:00"
   }
   ```
4. Server updates only the specified fields, leaving others at defaults
5. Alice verifies: `GET /notifications/preferences` shows updated values
6. The next morning, briefing fires at 7am instead of 8am
7. At noon, no midday nudge is sent (disabled)
8. The evening reflection at 8pm still fires (within allowed hours)

## Satisfaction Criteria
- Preferences are per-user and persist across sessions
- Partial update: only specified fields change
- Time values are stored as TIME without timezone (interpreted in user's timezone)
- Quiet hours that span midnight (e.g., 22:00 to 07:00) are handled correctly
- Disabling a notification type immediately stops that notification
- Re-enabling a notification type takes effect from the next scheduled time

## Failure Modes
- Setting a time like "25:00" returns 422
- Setting quiet_hours_start without quiet_hours_end returns 422 (must set both or neither)
- Setting quiet_hours that cover the entire day (start == end) returns 422

## Satisfaction Score Rubric
- **1.0**: Full CRUD for preferences, partial updates, midnight-spanning quiet hours, immediate effect
- **0.8**: Preferences work but quiet hours that span midnight are buggy
- **0.5**: Preferences can be read and written but don't affect notification delivery
- **0.2**: Endpoint exists but validation is missing
- **0.0**: No preference management
