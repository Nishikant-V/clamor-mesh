
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from database import Base, engine
from models import Message, Node, Report, User  # noqa: F401
from packets import esp_manager
from packets.packet_handler import mark_stale_nodes_offline

# Routers
from routes import (
    ai_router,
    debug_router,
    messages_router,
    nodes_router,
    reports_router,
    stats_router,
    users_router,
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OFFLINE_SWEEP_INTERVAL = 5

ENABLE_BLE = os.getenv("ENABLE_BLE", "0") == "1"

DEBUG = os.getenv("DEBUG", "1") != "0"

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")
    if origin.strip()
]


# --------------------------------------------------
# Database compatibility
# --------------------------------------------------

def _ensure_report_columns() -> None:
    """Add missing report columns to existing databases."""

    try:
        inspector = inspect(engine)
        columns = {
            column["name"]
            for column in inspector.get_columns("reports")
        }
    except Exception:
        logger.exception("Could not inspect reports table")
        return

    statements = []

    if "cluster_id" not in columns:
        statements.append(
            "ALTER TABLE reports ADD COLUMN cluster_id VARCHAR(64)"
        )
        statements.append(
            "CREATE INDEX IF NOT EXISTS "
            "ix_reports_cluster_id ON reports (cluster_id)"
        )

    if "cluster_summary" not in columns:
        statements.append(
            "ALTER TABLE reports ADD COLUMN cluster_summary VARCHAR(600)"
        )

    if "cluster_responders" not in columns:
        statements.append(
            "ALTER TABLE reports ADD COLUMN cluster_responders JSON"
        )

    added_resolved = "resolved" not in columns

    if added_resolved:
        statements.append(
            "ALTER TABLE reports ADD COLUMN "
            "resolved BOOLEAN NOT NULL DEFAULT FALSE"
        )

    if not statements:
        return

    with engine.begin() as connection:

        for statement in statements:
            connection.execute(text(statement))

        if added_resolved:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_reports_resolved ON reports (resolved)"
                )
            )

            connection.execute(
                text(
                    "UPDATE reports SET resolved = TRUE "
                    "WHERE lower(status) IN ('resolved', 'closed')"
                )
            )

    logger.info(
        "Database compatibility updates completed: %s",
        len(statements)
    )


# --------------------------------------------------
# Background tasks
# --------------------------------------------------

async def _offline_sweep():

    while True:

        try:
            marked = await asyncio.to_thread(
                mark_stale_nodes_offline
            )

            if marked:
                logger.info(
                    "Marked %s node(s) offline",
                    marked
                )

        except Exception:
            logger.exception("Offline sweep error")

        await asyncio.sleep(OFFLINE_SWEEP_INTERVAL)


# --------------------------------------------------
# FastAPI lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting FastAPI backend...")

    # Initialize database tables
    Base.metadata.create_all(bind=engine)

    # Apply compatibility updates
    _ensure_report_columns()

    # Baseline clustering for existing reports
    from ai.cluster import enqueue_baseline

    enqueue_baseline()

    # Start background tasks
    tasks = []

    # Bluetooth is disabled by default in cloud hosting
    if ENABLE_BLE:

        logger.info("Starting ESP32 Bluetooth connection...")

        ble_task = asyncio.create_task(
            esp_manager.connect_to_esp32()
        )

        tasks.append(ble_task)

    else:
        logger.info("Bluetooth disabled (ENABLE_BLE=0)")

    # Monitor stale nodes
    sweep_task = asyncio.create_task(
        _offline_sweep()
    )

    tasks.append(sweep_task)

    logger.info("FastAPI backend started successfully")

    try:
        yield

    finally:

        logger.info("Stopping FastAPI backend...")

        # Cancel background tasks
        for task in tasks:
            task.cancel()

        await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        logger.info("FastAPI backend stopped")


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="net0 Portal",
    lifespan=lifespan
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API routers
# --------------------------------------------------

app.include_router(users_router)
app.include_router(nodes_router)
app.include_router(reports_router)
app.include_router(messages_router)
app.include_router(stats_router)
app.include_router(ai_router)


# Debug routes
if DEBUG:

    app.include_router(debug_router)

else:

    logger.info("DEBUG routes disabled (DEBUG=0)")


# --------------------------------------------------
# Static files
# --------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"

STATIC_DIR.mkdir(exist_ok=True)

if STATIC_DIR.exists():

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static"
    )


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
async def root():

    return {
        "status": "online",
        "service": "net0 Portal"
    }


# --------------------------------------------------
# Debug page
# --------------------------------------------------

@app.get("/debug", include_in_schema=False)
async def debug_page():

    idx = STATIC_DIR / "debug.html"

    if idx.exists():

        return FileResponse(str(idx))

    return {
        "detail": "debug.html not found",
        "hint": "Check portal-end/backend/static/debug.html"
    }
