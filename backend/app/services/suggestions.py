"""Task ordering suggestion service."""
import json

from app.core.llm import get_llm_client
from app.models.task import Task


SUGGESTION_PROMPT = """Given tasks and user productivity patterns, suggest optimal order for today.
Return ONLY JSON:
{
    "task_order": ["id1", "id2", ...],
    "reasoning": [{"task_id": "...", "reason": "..."}],
    "warnings": [{"task_id": "...", "message": "..."}]
}"""


class SuggestionService:
    """Service for AI-powered task ordering suggestions."""

    def __init__(self):
        self.llm = get_llm_client()

    async def suggest_order(
        self, tasks: list[Task], patterns: list[dict]
    ) -> dict:
        """Suggest optimal task ordering based on patterns and task properties.

        Args:
            tasks: List of user's tasks
            patterns: User's productivity patterns

        Returns:
            Suggestion with task_order, reasoning, and warnings
        """
        task_data = [
            {
                "id": str(t.id),
                "title": t.title,
                "priority": t.priority,
                "due_date": str(t.due_date) if t.due_date else None,
                "category": t.category,
                "estimated_minutes": t.estimated_minutes,
            }
            for t in tasks
        ]

        messages = [
            {"role": "system", "content": SUGGESTION_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "tasks": task_data,
                        "patterns": patterns,
                    }
                ),
            },
        ]

        try:
            result = await self.llm.complete_json(messages, temperature=0.0)
            return result
        except Exception:
            # Fallback: rule-based ordering
            sorted_tasks = sorted(
                tasks,
                key=lambda t: (-t.priority, str(t.due_date or "9999-12-31")),
            )
            return {
                "task_order": [str(t.id) for t in sorted_tasks],
                "reasoning": [],
                "warnings": [],
            }

    def rule_based_suggest(self, tasks: list[Task]) -> dict:
        """Fallback rule-based suggestion when LLM is unavailable."""
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-t.priority, str(t.due_date or "9999-12-31")),
        )
        return {
            "task_order": [str(t.id) for t in sorted_tasks],
            "reasoning": [],
            "warnings": [],
        }