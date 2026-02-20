# Meridian Project Conventions

## Code Style

### Python (Backend)

- **Python version**: 3.12+
- **Formatting**: Black (optional, but consistent formatting encouraged)
- **Type hints**: Required for all function signatures
- **Imports**: Absolute imports only
- **Async/Await**: Use throughout the codebase for I/O operations
- **Naming**:
  - Classes: PascalCase (e.g., `TaskModel`)
  - Functions/variables: snake_case (e.g., `get_task_by_id`)
  - Constants: UPPER_SNAKE_CASE (e.g., `MAX_TASKS_PER_DAY`)

### Frontend (React/TypeScript)

- **TypeScript**: Strict mode enabled
- **Component style**: Functional components with hooks
- **Styling**: Tailwind CSS only
- **State management**: Zustand for global state
- **Data fetching**: TanStack Query for all API calls
- **Naming**:
  - Components: PascalCase (e.g., `TaskList`)
  - Hooks: useXxx (e.g., `useTaskStore`)
  - Variables/funcs: camelCase

## Project Structure

### Backend

```
backend/
├── app/
│   ├── core/          # Core utilities (config, security, db, redis, llm)
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── routers/       # FastAPI routers (API endpoints)
│   ├── services/      # Business logic layer
│   ├── tasks/         # Celery task definitions
│   └── main.py        # FastAPI app factory
├── tests/             # Test suite
│   ├── conftest.py    # Test fixtures
│   └── test_*.py      # Individual test files
├── alembic/           # Database migrations
├── pyproject.toml
└── alembic.ini
```

### Frontend

```
frontend/
├── src/
│   ├── api/           # API client utilities
│   ├── components/    # React components
│   │   ├── ui/        # Reusable UI components
│   │   ├── auth/      # Auth-related components
│   │   ├── tasks/     # Task-related components
│   │   └── planning/  # Planning-related components
│   ├── pages/         # Page-level components
│   ├── stores/        # Zustand state stores
│   ├── types/         # TypeScript types
│   ├── App.tsx
│   └── main.tsx
├── tests/
├── public/
├── package.json
└── vite.config.ts
```

## Database

- Use PostgreSQL 16
- Use async SQLAlchemy 2.0
- Use Alembic for migrations
- All tables use UUID primary keys
- All timestamps are timezone-aware (TIMESTAMPTZ)
- Use transactional rollback in tests

## API Conventions

- **Base path**: `/api/v1`
- **Authentication**: Bearer token in `Authorization` header
- **Pagination**: Cursor-based pagination for list endpoints
- **Error format**:
  ```json
  {
    "detail": {
      "code": "RESOURCE_ERROR_TYPE",
      "message": "Human-readable message",
      "field": "field_name_or_null"
    }
  }
  ```
- **Status codes**:
  - 200: Success
  - 201: Created
  - 400: Bad request
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not found
  - 422: Validation error
  - 500: Server error

## LLM Integration

- All LLM calls go through `app.core.llm.get_llm_client()`
- Tests use mock LLM client (never call real llama.cpp during tests)
- Intelligence features have rule-based fallbacks
- LLM errors are non-critical (app works without model)

## Testing

- **Backend**: pytest + pytest-asyncio
- **Frontend**: Vitest + Testing Library + MSW
- **Test naming**: `test_{action}_{condition}_{expected_result}`
- **Test isolation**: Each test uses fresh database

## Security

- Passwords hashed with bcrypt (min 12 rounds)
- JWT tokens: access (15min), refresh (7 days)
- CORS configured explicitly
- Rate limiting on auth endpoints

## Configuration

- Environment variables via Pydantic Settings
- `.env` file for local development
- `.env.example` with defaults provided
- No hardcoded secrets

## Deployment

- Docker Compose for local development
- Production environment variables required:
  - `JWT_SECRET` (strong random string)
  - `SMTP_*` (for email sending)
  - `VAPID_*` (for push notifications)