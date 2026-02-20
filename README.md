# Meridian - Daily Task Organizer

A web-based daily task organizer with smart notifications and intelligence powered by a local LLM.

## Overview

Meridian helps you plan your day effectively with:

- **Task Management**: Create, organize, and track tasks with priorities and categories
- **Daily Planning**: Plan your day with ordered task lists and reflection
- **Smart Notifications**: Morning briefings, midday nudges, and evening reflections
- **AI Intelligence**: Pattern detection and AI-powered task ordering (via local llama.cpp)

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7 (sessions, Celery broker)
- **Task Queue**: Celery 5 with Redis broker
- **Frontend**: React 18, TypeScript, TanStack Query, Tailwind CSS, dnd-kit
- **Auth**: JWT access/refresh tokens, bcrypt, Google OAuth 2.0
- **Notifications**: Web Push (VAPID), email (SMTP via Celery)
- **LLM**: Qwen3-Coder via llama.cpp at localhost:8085

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- llama.cpp running on localhost:8085 with Qwen3-Coder model

## Quick Start

1. Start your infrastructure:
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Start the backend
cd backend
uv sync
alembic upgrade head
uvicorn app.main:app --reload

# Start Celery workers
celery -A app.tasks worker -l info

# Start the frontend
cd frontend
pnpm install
pnpm dev
```

2. Make sure llama.cpp is running:
```bash
curl http://localhost:8085/health  # should return 200
```

3. Access the app at http://localhost:3000

## Development

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Run migrations
alembic upgrade head

# Run tests
pytest -v

# Run server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Run development server
pnpm dev

# Run tests
pnpm test

# Run lint
pnpm lint
```

## Environment Variables

See `.env.example` for all available options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret for JWT tokens
- `LLM_BASE_URL`: URL to llama.cpp server (default: http://localhost:8085)
- `SMTP_*`: Email configuration

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Project Structure

```
meridian-project/
├── backend/
│   ├── app/
│   │   ├── core/      # Config, security, database
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── routers/   # FastAPI routers
│   │   ├── services/  # Business logic
│   │   ├── tasks/     # Celery tasks
│   │   └── main.py    # FastAPI app
│   ├── tests/         # Test suite
│   ├── alembic/       # Database migrations
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/       # API client
│   │   ├── components/# React components
│   │   ├── pages/     # Page components
│   │   ├── stores/    # Zustand stores
│   │   └── App.tsx
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Testing

Run the full test suite:

```bash
# Backend tests
cd backend
pytest -v --cov=app

# Frontend tests
cd frontend
pnpm test

# Integration tests (requires llama.cpp)
LLM_INTEGRATION_TESTS=1 pytest
```

## License

MIT