# Scenario 17: AI-Powered Task Ordering Suggestions

## Phase
Intelligence

## User Story
Alice opens her daily planning view. Before she starts dragging tasks, Meridian suggests an optimized order based on her detected patterns — putting high-energy tasks in the morning when she's most productive, and flagging a task she's likely to skip.

## Preconditions
- Alice has 14+ days of pattern data
- Alice has 6 pending tasks for today
- Patterns indicate: peak productivity in morning, underestimates work tasks, rarely completes personal tasks on weekdays

## Steps
1. Alice opens the planning view for today
2. Frontend calls `GET /intelligence/suggestions?date=2025-01-15`
3. Server retrieves Alice's patterns and today's candidate tasks
4. Server calls the LLM (or uses a rule-based algorithm) to produce:
   ```json
   {
     "suggested_order": ["task_id_1", "task_id_3", "task_id_5", "task_id_2", "task_id_6", "task_id_4"],
     "reasoning": [
       {"task_id": "task_id_1", "reason": "High energy task — scheduled for your peak morning hours"},
       {"task_id": "task_id_3", "reason": "Due today — prioritized to avoid missing deadline"},
       {"task_id": "task_id_4", "reason": "Personal task on a weekday — you complete these 20% of the time. Consider moving to Saturday."}
     ],
     "warnings": [
       {"task_id": "task_id_2", "type": "underestimate", "message": "You estimated 60 min for this work task. Based on your history, it may take ~100 min."}
     ],
     "total_estimated_minutes": 320,
     "adjusted_estimated_minutes": 410
   }
   ```
5. Frontend shows the suggested order with reasoning tooltips
6. Alice can accept the suggestion (one click applies the order) or ignore it and drag manually
7. If Alice accepts, `POST /plans/2025-01-15` is called with the suggested order

## Satisfaction Criteria
- Suggestions are based on real pattern data, not random
- Each suggestion includes a human-readable reason
- Warnings about underestimates include the adjusted time
- Flagged tasks (likely to skip) include the historical skip rate
- The suggestion endpoint responds in <3 seconds
- Suggestions are optional — the user can always override
- If no patterns exist yet, the endpoint returns a basic order (by priority + due date) with no reasoning
- The LLM is only called if rule-based ordering isn't sufficient; for simple cases, rules are faster

## Failure Modes
- LLM timeout → fall back to rule-based ordering (priority + due date)
- User has no patterns → return priority-sorted order with message "More data needed for personalized suggestions"
- All tasks are the same priority → order by due date, then by estimated time (shortest first)

## Satisfaction Score Rubric
- **1.0**: Pattern-based suggestions with reasoning, warnings, adjusted estimates, <3s response, graceful fallback
- **0.8**: Suggestions work but reasoning is missing or generic
- **0.5**: Returns an order but based on simple rules only, not patterns
- **0.2**: Endpoint exists but returns tasks in arbitrary order
- **0.0**: No suggestion capability
