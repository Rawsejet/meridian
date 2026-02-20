# Meridian — LLM Client Spec

## 1. Purpose

Meridian's intelligence features (natural language task capture, AI suggestions) call an LLM at runtime. The LLM is the same local llama.cpp server that the coding agent uses to build Meridian.

There is no multi-provider abstraction. There is one model, one server, one endpoint.

## 2. Infrastructure

```
Model:        Qwen3-Coder (UD-Q8_K_XL quantization)
Server:       llama.cpp
Endpoint:     http://localhost:8085/v1/chat/completions
Health:       http://localhost:8085/health
Context:      262,144 tokens
GPU:          Dual RTX PRO 6000 (45/55 split)
```

From inside Docker containers, the endpoint is `http://host.docker.internal:8085/v1/chat/completions`.

## 3. Configuration

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # ... other settings ...

    llm_base_url: str = "http://localhost:8085"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1     # low for structured extraction
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_prefix="", env_file=".env")
```

```env
# .env (host) or docker env
LLM_BASE_URL=http://localhost:8085          # on host
# LLM_BASE_URL=http://host.docker.internal:8085  # inside docker
```

## 4. Client

```python
# backend/app/core/llm.py

import httpx
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for the local llama.cpp server (OpenAI-compatible API)."""

    def __init__(self, base_url: str, max_tokens: int = 2048, temperature: float = 0.1, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.http = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """
        Send a chat completion request. Returns the assistant's text.

        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        json_mode: if True, requests JSON output format
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = await self.http.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]

        usage = data.get("usage", {})
        logger.info(
            "LLM call: tokens_in=%d tokens_out=%d",
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        return content

    async def complete_json(self, messages: list[dict], **kwargs) -> dict:
        """Complete and parse as JSON. Raises ValueError if parse fails."""
        text = await self.complete(messages, json_mode=True, **kwargs)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def health_check(self) -> bool:
        """Check if llama.cpp is responding."""
        try:
            resp = await self.http.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self):
        await self.http.aclose()


# --- Singleton ---

_client: LLMClient | None = None

def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        from app.core.config import get_settings
        s = get_settings()
        _client = LLMClient(
            base_url=s.llm_base_url,
            max_tokens=s.llm_max_tokens,
            temperature=s.llm_temperature,
            timeout=s.llm_timeout_seconds,
        )
    return _client
```

That's the entire LLM abstraction. ~60 lines.

## 5. Usage: Natural Language Task Parsing

```python
# backend/app/services/task_parser.py

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
    def __init__(self):
        self.llm = get_llm_client()

    async def parse(self, text: str, timezone: str, today: str) -> dict:
        messages = [
            {"role": "system", "content": TASK_PARSE_PROMPT.format(timezone=timezone, today=today)},
            {"role": "user", "content": text},
        ]
        try:
            return await self.llm.complete_json(messages, temperature=0.0)
        except Exception:
            return {"title": text[:500], "description": None, "due_date": None,
                    "priority": 2, "estimated_minutes": None, "energy_level": None, "category": None}
```

## 6. Usage: Task Ordering Suggestions

```python
# backend/app/services/suggestions.py

SUGGESTION_PROMPT = """Given tasks and user productivity patterns, suggest optimal order for today.
Return ONLY JSON:
{{"task_order": ["id1", "id2", ...], "reasoning": [{{"task_id": "...", "reason": "..."}}], "warnings": [{{"task_id": "...", "message": "..."}}]}}"""


class SuggestionService:
    def __init__(self):
        self.llm = get_llm_client()

    async def suggest_order(self, tasks: list, patterns: list) -> dict:
        messages = [
            {"role": "system", "content": SUGGESTION_PROMPT},
            {"role": "user", "content": json.dumps({"tasks": [...], "patterns": [...]})},
        ]
        try:
            return await self.llm.complete_json(messages, temperature=0.0)
        except Exception:
            # Rule-based fallback: priority desc, then due date asc
            sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, t.due_date or "9999-12-31"))
            return {"task_order": [str(t.id) for t in sorted_tasks], "reasoning": [], "warnings": []}
```

## 7. Error Handling

Every LLM-powered feature has a non-LLM fallback. The app works without the model running.

| Failure | Detection | Recovery |
|---|---|---|
| Server not running | `httpx.ConnectError` | Return fallback, log warning |
| Timeout | `httpx.ReadTimeout` | Return fallback |
| Bad JSON from model | `json.JSONDecodeError` | Retry once, then fallback |
| HTTP 503 (overloaded) | Status code | Retry once after 2s, then fallback |

## 8. Testing

**Unit tests use a mock, never the real server:**

```python
# backend/tests/conftest.py

class MockLLMClient:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)
        self.calls: list[dict] = []

    async def complete(self, messages, **kwargs):
        self.calls.append({"messages": messages, **kwargs})
        return next(self._responses)

    async def complete_json(self, messages, **kwargs):
        text = await self.complete(messages, **kwargs)
        return json.loads(text)

    async def health_check(self):
        return True

    async def close(self):
        pass


@pytest.fixture
def mock_llm(monkeypatch):
    """Override get_llm_client with a mock. Set mock.responses before use."""
    mock = MockLLMClient([])
    monkeypatch.setattr("app.core.llm.get_llm_client", lambda: mock)
    return mock
```

**Real-LLM tests gated behind env var:**

```python
@pytest.mark.skipif(os.getenv("LLM_INTEGRATION_TESTS") != "1", reason="Requires live llama.cpp")
async def test_nl_parsing_real_model():
    client = LLMClient(base_url="http://localhost:8085")
    result = await client.complete_json([
        {"role": "system", "content": TASK_PARSE_PROMPT.format(timezone="UTC", today="2025-01-15")},
        {"role": "user", "content": "Buy groceries tomorrow high priority 30 min"},
    ], temperature=0.0)
    assert result["title"]
    assert result["priority"] >= 3
    assert result["due_date"] == "2025-01-16"
```

Run manually when the coding agent is idle: `LLM_INTEGRATION_TESTS=1 pytest tests/test_intelligence.py -v`

## 9. Health Check Integration

The backend health endpoint reports llama.cpp status:

```python
@router.get("/health")
async def health():
    llm_ok = await get_llm_client().health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "llm": "connected" if llm_ok else "disconnected",  # informational, not critical
    }
```

The LLM being down is **not** a critical health failure — the app still works, just without intelligence features. The health endpoint reports it as informational.
