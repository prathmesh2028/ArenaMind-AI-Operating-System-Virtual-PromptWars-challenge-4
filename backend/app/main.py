"""
ArenaMind AI — FastAPI Application Entry Point
===============================================
Bootstraps the application with:
  - Database initialization
  - Digital Twin background task (lifespan)
  - CORS middleware
  - Rate limiting middleware
  - Request logging middleware
  - Global exception handlers
  - All API routers
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middleware
from app.database import Base, engine, get_db
from app.engine.twin import start_twin, stop_twin, get_twin_status
from app.engine.prediction import prediction_engine
from app.engine.decision import decision_engine

# Event Bus & Handlers
from app.bus.core import bus
from app.bus.handlers import register_all_handlers
from app.bus.router import router as bus_router

# Routers
from app.routers import auth, events, incidents, predictions, tasks, replay, dashboard, fan, volunteer, operations, decisions as decisions_router, copilot as copilot_router

# ---------------------------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("arenamind")


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup → serve → shutdown lifecycle."""

    # Startup
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ready.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    logger.info("Registering Event Bus handlers...")
    register_all_handlers(bus)

    logger.info("Registering Prediction Engine listeners...")
    prediction_engine.register_listeners(bus)

    logger.info("Registering Decision Engine listeners...")
    decision_engine.register_listeners(bus)

    logger.info("Starting Event Bus...")
    await bus.start()

    logger.info("Starting Digital Twin simulation engine...")
    twin_task = asyncio.create_task(start_twin(tick_interval_seconds=5.0))
    logger.info("Digital Twin is running.")

    yield  # Application is live

    # Shutdown
    logger.info("Shutting down Digital Twin...")
    stop_twin()
    twin_task.cancel()
    try:
        await twin_task
    except asyncio.CancelledError:
        pass

    logger.info("Stopping Event Bus...")
    await bus.stop()

    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI App Instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ArenaMind AI API",
    description=(
        "## The Intelligent Stadium Operating System\n\n"
        "ArenaMind AI is a real-time, AI-powered stadium operations platform for FIFA World Cup 2026.\n\n"
        "### Key Features\n"
        "- 🏟️ **Digital Twin** — Live stadium simulation with 5s telemetry ticks\n"
        "- 🚨 **Incident Management** — Automated detection, escalation & resolution\n"
        "- 🤖 **AI Predictions** — Probabilistic crowd congestion forecasting\n"
        "- 🚌 **Transport** — Live shuttle, bus, and train GPS tracking\n"
        "- ⚡ **Energy** — Real-time grid load monitoring and carbon tracking\n"
        "- 👥 **Role-Based Access** — ADMIN, OPERATIONS, VOLUNTEER, MEDICAL, SECURITY, FAN\n\n"
        "### Authentication\n"
        "Use **POST /auth/login** with a seed user email to obtain a Bearer JWT token.\n\n"
        "**Demo users:**\n"
        "- `manager@fifa.com` (OPERATIONS)\n"
        "- `volunteer1@fifa.com` (VOLUNTEER)\n"
        "- `medical1@fifa.com` (MEDICAL)\n"
        "- `fan1@gmail.com` (FAN)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Register Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_middleware(app)

# ---------------------------------------------------------------------------
# Register Exception Handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(tasks.router)
app.include_router(replay.router)
app.include_router(dashboard.router)
app.include_router(fan.router)
app.include_router(volunteer.router)
app.include_router(operations.router)
app.include_router(bus_router)
app.include_router(decisions_router.router)
app.include_router(copilot_router.router)


# ---------------------------------------------------------------------------
# System Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Database connectivity and service health check."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
            "database": "connected",
            "twin": get_twin_status(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )


@app.get("/twin/status", tags=["Digital Twin"])
def twin_status_route():
    """Return a live snapshot of the Digital Twin simulation state."""
    return get_twin_status()
