# Scenario 15: Natural Language Task Capture

## Phase
Intelligence

## User Story
Alice quickly adds a task by typing a natural language sentence. The system parses it into a structured task with title, due date, priority, time estimate, and category — all inferred from the text.

## Preconditions
- Alice is authenticated
- LLM client is configured (Claude API or local vLLM)
- Alice's timezone is America/Los_Angeles, today is 2025-01-15

## Steps
1. Alice types: "Buy groceries tomorrow afternoon, high priority, should take about 30 minutes"
2. Frontend sends `POST /tasks/parse` with `{"text": "Buy groceries tomorrow afternoon, high priority, should take about 30 minutes"}`
3. Server calls the LLM with the task parsing system prompt
4. LLM returns structured JSON:
   ```json
   {
     "title": "Buy groceries",
     "due_date": "2025-01-16",
     "priority": 3,
     "estimated_minutes": 30,
     "energy_level": 1,
     "category": "errands",
     "description": null
   }
   ```
5. Server validates the parsed output against the task schema
6. Server returns the parsed task to the frontend for confirmation
7. Alice reviews, adjusts the category to "shopping", and confirms
8. Frontend sends `POST /tasks` with the confirmed data to actually create the task

## Additional Parsing Examples
- "Prepare the Q4 deck for Friday, gonna need a couple hours, it's mentally draining" → title: "Prepare Q4 deck", due_date: next Friday, priority: 2, estimated_minutes: 120, energy_level: 3, category: "work"
- "Call mom" → title: "Call mom", everything else null/default (minimal input)
- "URGENT: server is down, fix immediately" → title: "Fix server outage", priority: 4, energy_level: 3, category: "work"
- "Maybe look into that new framework sometime" → title: "Research new framework", priority: 1, energy_level: 2, category: "learning"

## Satisfaction Criteria
- The parse endpoint returns parsed data but does NOT create the task (two-step: parse then confirm)
- Relative dates ("tomorrow", "next Friday", "this weekend") are correctly resolved using the user's timezone
- Priority keywords ("urgent", "high priority", "low priority", "whenever") are mapped correctly
- Time estimates ("30 minutes", "a couple hours", "half an hour") are parsed into minutes
- Energy level inferred from context ("mentally draining" → high, "quick errand" → low)
- Minimal input still works: "Call mom" returns just a title with defaults
- If the LLM returns invalid data (e.g., priority: 5), the server corrects it to the nearest valid value
- LLM errors are handled gracefully: return a fallback with just the raw text as the title

## Failure Modes
- Empty text returns 422
- LLM timeout → return fallback: `{"title": "<raw text>", ...defaults}`
- LLM returns unparseable response → retry once, then fallback
- Extremely long input (>1000 chars) → truncate before sending to LLM

## Satisfaction Score Rubric
- **1.0**: Robust parsing of all examples, graceful fallback, two-step flow, relative date resolution
- **0.8**: Parsing works for common cases but edge cases (minimal input, urgency) fail
- **0.5**: Endpoint exists and calls LLM but doesn't validate output or handle errors
- **0.2**: Endpoint exists but always returns raw text as title
- **0.0**: No NL parsing
