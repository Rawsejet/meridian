# Scenario 19: Docker Stack Boot and Health Check

## Phase
Integration

## User Story
A developer (or CI system) runs `docker compose up` and the entire Meridian stack comes up healthy: database, Redis, backend API, Celery worker, Celery beat, and frontend.

## Preconditions
- Docker and Docker Compose are installed
- `.env` file is populated from `.env.example`
- No services are running on ports 5432, 6379, 8000, 3000

## Steps
1. Run `docker compose up -d`
2. PostgreSQL starts and accepts connections within 15 seconds
3. Redis starts and responds to PING within 5 seconds
4. Backend runs Alembic migrations on startup (or via an init container)
5. Backend starts FastAPI on port 8000
6. `GET /health` returns:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "redis": "connected",
     "version": "0.1.0"
   }
   ```
7. Celery worker connects to Redis broker and reports ready
8. Celery beat starts and registers the periodic task schedule
9. Frontend builds and serves on port 3000
10. Frontend loads in the browser and shows the login page

## Satisfaction Criteria
- All services start without errors in `docker compose logs`
- Backend waits for database readiness before attempting migrations (not a race condition)
- Health endpoint checks actual database and Redis connectivity (not just returns 200)
- If database is down, health returns `{"status": "unhealthy", "database": "disconnected"}`
- Frontend can reach the backend API (CORS configured correctly)
- The entire stack boots in under 60 seconds on a reasonable machine
- `docker compose down -v` cleanly removes all containers and volumes

## Failure Modes
- Database not ready when backend starts → backend retries connection with backoff, or uses depends_on with healthcheck
- Port conflict → clear error message identifying which port
- Missing env vars → backend fails fast with clear error listing missing variables
- Frontend build fails → npm install + build logs are visible in docker compose logs

## Satisfaction Score Rubric
- **1.0**: Clean boot, all services healthy, proper dependency ordering, health checks accurate, <60s
- **0.8**: All services start but health check is shallow (just returns 200)
- **0.5**: Most services start but Celery doesn't connect or frontend CORS is broken
- **0.2**: Docker compose file exists but services crash on start
- **0.0**: No Docker setup
