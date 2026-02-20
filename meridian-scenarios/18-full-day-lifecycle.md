# Scenario 18: Full Day Lifecycle — End to End

## Phase
Integration

## User Story
This scenario traces a complete day in Alice's life with Meridian: from morning briefing to evening reflection, covering every major system interaction.

## Preconditions
- Alice is a 2-week user with established patterns
- She has 8 pending tasks, some from yesterday, some newly created
- Her notification preferences: morning 7am, midday noon, evening 8pm, all enabled

## Timeline

### 7:00 AM — Morning Briefing
1. Celery fires morning briefing for Alice
2. Push notification: "Good morning, Alice! You have 8 tasks available. Ready to plan your day?"
3. Email with the same content arrives

### 7:15 AM — Daily Planning
4. Alice opens the app, sees the planning view
5. AI suggestion endpoint recommends an order for 6 of her 8 tasks (leaving 2 for later)
6. She accepts the suggestion with one modification (swaps positions 2 and 3)
7. Plan saved: 6 tasks in her custom order

### 8:30 AM — Task Work
8. Alice starts her first task. She marks it in-progress (optional status)
9. She completes it in 45 minutes (estimated: 30 min)
10. She marks it complete via `POST /tasks/{id}/complete` with actual_minutes: 45

### 10:00 AM — Quick Task Add
11. Alice types: "Pick up dry cleaning on the way home, low priority"
12. NL parser returns: title "Pick up dry cleaning", priority 1, category "errands"
13. She confirms and adds it to today's plan (plan now has 7 tasks)

### 12:00 PM — Midday Nudge
14. Celery checks Alice's progress: 1/7 tasks done (14%)
15. Nudge sent: "You've completed 1 task so far. Next up: [task #2]. Keep going!"

### 2:00 PM — Progress
16. Alice completes 3 more tasks
17. Current status: 4/7 done

### 5:00 PM — Decision to Skip
18. Alice decides she won't get to task #6 today
19. She doesn't do anything yet — she'll mark it in reflection

### 8:00 PM — Evening Reflection
20. Reflection prompt: "You completed 4 out of 7 tasks today (57%). Ready to reflect?"
21. Alice opens reflection modal:
    - Tasks 1-4: completed with actual times
    - Task 5: completed (just finished)
    - Task 6: skipped, reason: "Ran out of time, reschedule to tomorrow"
    - Task 7 (dry cleaning): completed, 10 minutes
22. Mood: 3 (okay day)
23. Note: "Good morning, lost steam after lunch"
24. Submits reflection

### 2:00 AM — Nightly Analysis
25. Pattern detection job runs
26. Updates Alice's patterns: her post-lunch productivity confirms the existing pattern
27. Estimation accuracy for her task #1 category updated (she underestimated by 50%)

## Satisfaction Criteria
- All 25 steps complete without errors
- Notifications fire at the correct local times
- Task completion counts are accurate at each checkpoint
- The midday nudge correctly reflects 1/7 completion
- The evening reflection correctly reflects 5/7 completion (she completed task 5 before reflection)
- The NL-added task (dry cleaning) integrates into the existing plan seamlessly
- The nightly job processes the new completion data
- All API responses are <500ms (excluding LLM calls which may be <3s)

## Satisfaction Score Rubric
- **1.0**: All 25 steps work flawlessly, timing is correct, data integrity maintained throughout
- **0.8**: Full flow works but one notification fires at wrong time or stats are off by 1
- **0.6**: Core flow works (plan → complete → reflect) but notifications or NL parsing broken
- **0.4**: Can plan and complete tasks but reflection or pattern detection doesn't work
- **0.2**: Basic task CRUD works but planning flow is broken
- **0.0**: Cannot complete the basic day cycle
