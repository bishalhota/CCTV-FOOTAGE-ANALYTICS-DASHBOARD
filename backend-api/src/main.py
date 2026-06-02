"""
Purpose: Main entry point for the FastAPI Backend.
Responsibilities:
- Initialize the FastAPI application and OpenAPI specifications.
- Configure Cross-Origin Resource Sharing (CORS) for the frontend dashboard.
- Register application lifespan hooks (startup/shutdown).
- Self-bootstrap the database on first startup (creates tables + seeds data).
- Mount the API routers.
Dependencies: fastapi
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from src.api.endpoints import stores, dashboard
from src.core.config import settings
from src.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


async def _bootstrap_database():
    """
    Self-bootstraps the database on first startup.
    Steps:
      1. Enable the pgvector extension (idempotent).
      2. Create all tables from SQLAlchemy metadata (idempotent via checkfirst=True).
      3. If the stores table is empty, run the full data seeder.
    This eliminates the need for a manual `docker exec` seed step.
    """
    from src.models import Base
    from src.models.store import Store

    logger.info("Running database bootstrap check...")

    # 1. Enable pgvector extension (required before any Vector column can be used)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension: OK")

    # 2. Create all tables (safe to run multiple times)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema: OK")

    # 3. Seed data only if the stores table is empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Store).limit(1))
        existing = result.scalars().first()

    if not existing:
        logger.info("Database is empty — running seeder...")
        try:
            from scripts.seed import seed_database
            await seed_database()
            logger.info("Database seeding: COMPLETE")
        except Exception as e:
            logger.error(f"Seeding failed (non-fatal, API will still start): {e}")
    else:
        logger.info("Database already seeded — skipping.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    Replaces the deprecated @app.on_event("startup") paradigm.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode...")

    # Self-bootstrap DB (idempotent — safe to run every container restart)
    await _bootstrap_database()

    yield

    logger.info("Gracefully shutting down backend services...")


# Initialize FastAPI with project metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production API for CCTV-based Store Intelligence.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS (Cross-Origin Resource Sharing)
# Critical: Without this, the React dashboard is blocked by the browser.
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount the routers under the versioned API prefix (e.g., /api/v1/stores)
app.include_router(stores.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"], status_code=status.HTTP_200_OK)
async def health_check():
    """
    Kubernetes / Load Balancer Health Check Endpoint.
    Returns service status, environment, and version.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }
