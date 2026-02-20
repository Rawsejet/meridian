# Scenario 10: Timezone-Aware Planning Across Date Boundaries

## Phase
Planning

## User Story
Alice lives in San Francisco (America/Los_Angeles, UTC-8). She creates a plan at 11pm her time (which is 7am UTC the next day). The plan should be for "today" in her timezone, not tomorrow in UTC.

## Preconditions
- Alice's profile has `timezone: "America/Los_Angeles"`
- Current time is 2025-01-15 23:00 PST (2025-01-16 07:00 UTC)

## Steps
1. Alice opens the daily planning view
2. Frontend determines "today" using Alice's timezone setting: `2025-01-15`
3. Alice creates a plan for `2025-01-15`
4. Server stores the plan with `plan_date: 2025-01-15` (the user's local date)
5. Next morning at 8am PST (2025-01-16 16:00 UTC), Alice opens the app
6. Frontend shows `2025-01-16` as today
7. Yesterday's plan (Jan 15) is in the history view
8. A new empty plan is presented for Jan 16

## Additional Steps — International User
1. Bob's timezone is `Asia/Tokyo` (UTC+9)
2. Bob creates a plan at 1am JST on January 16 (still January 15 in most of the world)
3. Bob's plan is correctly dated January 16 (his local date)
4. Meanwhile, Alice (in PST) sees January 15 as her current date at the same wall-clock moment

## Satisfaction Criteria
- `plan_date` is a DATE field (no time component) representing the user's local date
- The "today" determination happens based on the user's `timezone` setting, not server time
- All API date parameters are interpreted in the user's timezone context
- The server stores timestamps in UTC but converts for display
- Two users in different timezones can have plans for different dates at the same instant
- Due dates on tasks respect the user's timezone when checking "overdue"

## Failure Modes
- If the server uses UTC for date determination, late-night users get tomorrow's date
- If plan_date stores a datetime, timezone conversion produces wrong dates
- DST transitions: creating a plan at 1:30am during spring-forward (which doesn't exist) should gracefully handle the missing hour

## Satisfaction Score Rubric
- **1.0**: All timezone scenarios correct, DST handled, multi-timezone users work simultaneously
- **0.8**: Normal timezone handling works but DST edge case not covered
- **0.5**: Timezone field exists but "today" is calculated from server UTC
- **0.2**: No timezone support, everything uses UTC
- **0.0**: Dates are incorrect or inconsistent
