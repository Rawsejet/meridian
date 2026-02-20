"""Task parsing service for natural language input."""
from datetime import datetime, timedelta

from app.core.llm import get_llm_client
from app.schemas.intelligence import TaskParseResponse


TASK_PARSE_PROMPT = """You are a task parser for a daily planner app.
User timezone: {timezone} | Today: {today}

Extract structured fields from natural language input.
Return ONLY a JSON object:
- title (string, required)
- description (string or null)
- due_date (string YYYY-MM-DD or null, resolve relative dates from today)
- priority (integer 1-4, default 2)
- estimated_minutes (integer or null)
- energy_level (integer 1-3 or null)
- category (string or null)

No explanation, no markdown, just JSON."""


class TaskParserService:
    """Service for parsing natural language into structured task data."""

    def __init__(self):
        self.llm = get_llm_client()

    async def parse(self, text: str, timezone: str, today: str) -> TaskParseResponse:
        """Parse natural language into structured task data.

        Args:
            text: Natural language task description
            timezone: User's timezone
            today: Today's date in YYYY-MM-DD format

        Returns:
            Structured task data
        """
        messages = [
            {
                "role": "system",
                "content": TASK_PARSE_PROMPT.format(timezone=timezone, today=today),
            },
            {"role": "user", "content": text},
        ]

        try:
            result = await self.llm.complete_json(messages, temperature=0.0)
            return TaskParseResponse(**result)
        except Exception:
            # Fallback: treat entire text as title
            return TaskParseResponse(
                title=text[:500],
                description=None,
                due_date=None,
                priority=2,
                estimated_minutes=None,
                energy_level=None,
                category=None,
            )