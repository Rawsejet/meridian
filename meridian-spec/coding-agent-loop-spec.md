# Meridian — Coding Agent Loop Spec

## 1. Purpose

This document describes how the coding agent loop behaves when building Meridian. The agent is Claude Code pointed at a local Qwen3-Coder instance running on llama.cpp. This spec extends the general Attractor Coding Agent Loop spec with Meridian-specific conventions.

## 2. Provider Profile

```
ProviderProfile:
  provider: openai_compatible
  base_url: http://localhost:8085/v1
  model: qwen3-coder
  context_window_size: 262144
  max_output_tokens: 16384
  supports_parallel_tool_calls: true
  system_prompt: |
    You are building Meridian, a daily task organizer.
    Tech stack: FastAPI (Python 3.12+), PostgreSQL 16, Redis 7, Celery 5, React 18 + TypeScript.
    Follow the project conventions in CONVENTIONS.md at the repo root.
    Always run tests after making changes. Never leave broken tests.
    Use async/await throughout the FastAPI backend.
    Use Pydantic v2 for all request/response schemas.
    Use SQLAlchemy 2.0 async ORM patterns.
    Use TanStack Query for all frontend data fetching.
    The runtime LLM for intelligence features is this same server at localhost:8085.
```

**Note on context usage:** Qwen3-Coder at 262K context is generous, but the agent should still be mindful. Large files (>5000 lines) should be read in sections. The agent should prefer targeted file reads over dumping entire directories into context.

## 3. Execution Environment

```
ExecutionEnvironment:
  working_dir: /workspace/meridian
  shell: /bin/bash
  timeout_ms: 120000       # 2 minutes default
  max_file_size: 100000    # characters
  allowed_commands:
    - python, pip, uv, pytest, alembic, celery
    - node, npm, npx, vitest, tsc
    - docker, docker-compose
    - git, cat, ls, find, grep, head, tail, wc, diff, sed, awk
    - curl, psql, redis-cli
  blocked_patterns:
    - "rm -rf /"
    - "DROP DATABASE"
    - writes to /etc, /usr, /var outside docker volumes
```

## 4. Tool Set

### 4.1 `file_read`
Read a file's contents. Must read before writing (read-before-write guardrail).

### 4.2 `file_write`
Write content to a file. Creates parent directories if needed.

### 4.3 `file_edit`
String replacement in an existing file. `old_string` must match exactly once.

### 4.4 `shell`
Execute a shell command. Returns stdout, stderr, exit code. Enforces timeout.

### 4.5 `search`
Search file contents across the project using ripgrep-style patterns.

## 5. Agentic Loop

Standard Attractor loop: LLM call → tool execution → loop until natural completion (no tool calls in response).

```
LOOP:
  drain_steering(session)
  response = llm.complete(history, tools, system_prompt)
  history.append(response)

  IF no tool_calls in response:
    BREAK

  results = execute_tool_calls(response.tool_calls)
  history.append(results)

  IF consecutive_similar_failures >= 3:
    inject steering: "You've failed 3 times with similar errors. Re-read the relevant files and try a different approach."
```

## 6. Project Conventions

Codified in `CONVENTIONS.md` at the repo root. The agent creates this file during scaffolding.

### 6.1 Backend (Python/FastAPI)

```
backend/
  app/
    main.py              # FastAPI app factory
    core/
      config.py          # Pydantic Settings for env vars
      security.py        # JWT, password hashing
      database.py        # Async SQLAlchemy engine + session
      redis.py           # Redis connection pool
      llm.py             # LLM client for localhost:8085
    models/              # SQLAlchemy ORM models
    schemas/             # Pydantic v2 request/response schemas
    routers/             # FastAPI routers
    services/            # Business logic
    tasks/               # Celery task definitions
  tests/
    conftest.py          # Fixtures: async client, test DB, test user, mock LLM
    test_auth.py
    test_tasks.py
    test_plans.py
    test_notifications.py
    test_intelligence.py
    test_integration.py
  alembic/
    versions/
  pyproject.toml
  alembic.ini
```

**Rules:**
- All DB operations use `async with session.begin()`
- All endpoints return Pydantic response models
- All list endpoints use cursor-based pagination
- Passwords hashed with bcrypt, minimum 12 rounds
- JWT signed with HS256, secret from environment
- Env vars loaded via Pydantic Settings
- Tests use separate test database, transactional rollback per test
- All datetimes timezone-aware (UTC internal, user timezone for display)
- LLM calls go through `app/core/llm.py`, never direct httpx calls in services

### 6.2 Frontend (React/TypeScript)

```
frontend/
  src/
    api/
      client.ts          # Axios instance with JWT interceptor
      auth.ts
      tasks.ts
      plans.ts
    components/
      ui/                # Reusable (Button, Modal, etc.)
      tasks/
      planning/
      auth/
    hooks/
    pages/
    stores/              # Zustand (auth state)
    types/
    App.tsx
    main.tsx
  tests/
  index.html
  vite.config.ts
  tsconfig.json
  tailwind.config.ts
  package.json
```

**Rules:**
- All API calls through TanStack Query
- Auth state in Zustand with JWT persistence
- Axios interceptor: 401 → refresh → retry
- Tailwind CSS only
- Drag-and-drop: @dnd-kit/core + @dnd-kit/sortable
- Error boundaries at page level

### 6.3 Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: meridian
      POSTGRES_USER: meridian
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    depends_on: [db, redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://meridian:${DB_PASSWORD}@db:5432/meridian
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
      LLM_BASE_URL: http://host.docker.internal:8085
    ports: ["8000:8000"]

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker -l info
    depends_on: [db, redis]
    environment:
      LLM_BASE_URL: http://host.docker.internal:8085

  celery_beat:
    build: ./backend
    command: celery -A app.tasks beat -l info
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      VITE_API_URL: http://localhost:8000
```

**Note:** `LLM_BASE_URL` uses `host.docker.internal` so containers can reach llama.cpp running on the host at port 8085. On Linux, you may need `--add-host=host.docker.internal:host-gateway` or use the host's LAN IP.

## 7. Test Strategy

### 7.1 Backend Tests

Every test file uses:
- `async_client` fixture — httpx AsyncClient with the FastAPI test app
- `test_db` fixture — fresh test database with migrations, transactional rollback
- `auth_headers` fixture — `{"Authorization": "Bearer <token>"}` for a test user
- `mock_llm` fixture — patches `app.core.llm.get_llm_client()` with a mock returning canned responses

Test naming: `test_{action}_{condition}_{expected_result}`

**Critical:** Intelligence layer tests always use `mock_llm`. They never call the real llama.cpp server. The coding agent is using that server.

### 7.2 Frontend Tests

- Vitest + Testing Library
- MSW (Mock Service Worker) for API mocks
- Test interactions: form submission, drag sequences, modal open/close

### 7.3 Integration Tests

Single `test_integration.py`:
1. Register user → create 5 tasks → create plan → reorder → complete 3 tasks → submit reflection → verify stats → verify notification preferences

Real-LLM integration tests (NL parsing, suggestions against actual llama.cpp) are gated behind `LLM_INTEGRATION_TESTS=1` and skipped during pipeline execution.

## 8. Error Handling

All API errors return:
```json
{
  "detail": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID abc-123 not found",
    "field": null
  }
}
```

Pattern: `{RESOURCE}_{ERROR_TYPE}` — e.g., `AUTH_INVALID_CREDENTIALS`, `PLAN_DATE_CONFLICT`.

## 9. Loop Detection & Recovery

| Pattern | Detection | Recovery |
|---|---|---|
| Import cycle | Same `ImportError` 2+ times | Move shared types to `types.py` |
| Migration conflict | Alembic `FAILED` on upgrade | Drop test DB, recreate, re-run |
| Port in use | `Address already in use` | Kill process on that port, retry |
| Stale dependencies | `ModuleNotFoundError` | Run `uv sync` or `npm install` |
| Type error cascade | 3+ TS errors in same file | Re-read file, fix from root cause |
| Test DB state | Tests pass alone, fail together | Add teardown, use transactional isolation |
| llama.cpp unreachable | `ConnectionRefused` on :8085 | Check if llama.cpp is running, warn user |

## 10. Steering Hooks

The pipeline may inject steering between iterations:

- **Phase transition**: "Auth complete. Now implement task CRUD."
- **Test guidance**: "Timezone handling is failing. Store all times as UTC."
- **Human feedback**: "Reviewer says: make the drag handle more visible."

Steering messages are drained before each LLM call and appended to conversation history.
