# Scenario 16: Pattern Detection and Productivity Insights

## Phase
Intelligence

## User Story
After 2 weeks of using Meridian, Alice has enough data for pattern detection. The nightly job analyzes her task completions and discovers she's most productive in the morning, consistently underestimates work tasks, and rarely completes personal tasks on weekdays.

## Preconditions
- Alice has 14 days of daily plans with task completions
- Fixture data: Alice completed 85% of morning tasks, 40% of afternoon tasks; work task estimates average 60% of actual time; personal tasks on weekdays completed 20% of the time

## Steps — Nightly Pattern Job
1. Celery beat triggers the nightly pattern analysis job at 2am UTC
2. Job processes users with ≥7 days of data
3. For Alice, the job computes:
   - **Peak hours**: tasks planned in positions 1-3 (morning) have 85% completion vs 40% for positions 4+
   - **Estimation accuracy**: work tasks average 1.67x the estimated time (she underestimates)
   - **Category completion**: personal tasks on weekdays have 20% completion rate
   - **Completion rate trend**: improving — 50% week 1, 65% week 2
4. Job stores these as `user_patterns` records with confidence scores
5. Confidence increases as more data accumulates (sigmoid function of data points)

## Steps — Viewing Insights
1. Alice opens insights: `GET /intelligence/insights`
2. Response includes:
   ```json
   {
     "peak_productivity": {"time_range": "morning", "completion_rate": 0.85, "confidence": 0.72},
     "estimation_accuracy": {"category": "work", "ratio": 1.67, "suggestion": "Try multiplying your work estimates by 1.5x", "confidence": 0.68},
     "category_insights": [
       {"category": "personal", "weekday_completion": 0.20, "weekend_completion": 0.75, "suggestion": "Consider scheduling personal tasks on weekends"}
     ],
     "completion_trend": {"direction": "improving", "week_over_week_change": 0.15},
     "data_points": 14,
     "next_update": "2025-01-30T02:00:00Z"
   }
   ```

## Satisfaction Criteria
- Pattern detection requires minimum 7 days of data (returns empty before that)
- Confidence scores range 0.0-1.0 and increase with more data points
- Patterns are recomputed nightly, not on-demand (expensive operation)
- Insights endpoint reads from `user_patterns` table, not computing live
- Suggestions are concrete and actionable ("multiply work estimates by 1.5x" not "you underestimate")
- The `estimation_accuracy` pattern compares estimated_minutes to actual_minutes across completed tasks
- Categories with <3 tasks are excluded (insufficient data)
- The nightly job is idempotent (safe to re-run, overwrites existing patterns)

## Failure Modes
- User with <7 days of data → return `{"patterns": [], "message": "Need at least 7 days of data", "days_until_ready": N}`
- User with plans but no completions → return minimal insights (completion rate = 0)
- Nightly job timeout for users with huge datasets → process in batches, cap at 90 days of history

## Satisfaction Score Rubric
- **1.0**: All 4 pattern types detected, confidence scoring works, concrete suggestions, nightly batch job, minimum data threshold
- **0.8**: Patterns detected but confidence scoring is binary (0 or 1) instead of gradual
- **0.5**: Some patterns detected but suggestions are generic or missing
- **0.2**: Insights endpoint exists but returns empty/hardcoded data
- **0.0**: No pattern detection
