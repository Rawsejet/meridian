"""Main FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.core.database import get_engine, init_db, drop_db
from app.routers import auth, tasks, plans, notifications, intelligence


def get_middleware(settings: Settings) -> list[Middleware]:
    """Get middleware configuration."""
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application."""
    _settings = settings or get_settings()

    app = FastAPI(
        title="Meridian API",
        description="A daily task organizer with smart notifications and intelligence",
        version="0.1.0",
        middleware=get_middleware(_settings),
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Check if detail is a dict with a code
        if isinstance(exc.detail, dict):
            detail = exc.detail
            code = detail.get("code", "HTTP_ERROR")
            message = detail.get("message", str(exc.detail))
            field = detail.get("field")
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": {
                        "code": code,
                        "message": message,
                        "field": field,
                    }
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "field": None,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "code": "VALIDATION_ERROR",
                    "message": first_error.get("msg", "Validation failed"),
                    "field": first_error.get("loc", [None])[-1] if first_error.get("loc") else None,
                }
            },
        )

    # Include routers
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(plans.router, prefix="/api/v1", tags=["plans"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
    app.include_router(intelligence.router, prefix="/api/v1", tags=["intelligence"])

    # Health check
    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": "meridian"}

    return app


# Create app instance for development server
app = create_app()