from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ...config import Settings
from ...infrastructure.cache.redis_client import RedisClient
from ...infrastructure.database.timescale.connection import TimescaleDB
from ...infrastructure.messaging.kafka_producer import KafkaProducerClient
from .middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .routes import alerts, health, ingest, invariants, metrics, query


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application_starting")
    settings: Settings = app.state.settings

    # Database
    app.state.db = TimescaleDB(
        database_url=str(settings.database.url), pool_size=settings.database.pool_size
    )

    # Kafka
    app.state.kafka = KafkaProducerClient(bootstrap_servers=settings.kafka.bootstrap_servers)
    await app.state.kafka.start()

    # Redis
    app.state.redis = RedisClient(
        redis_url=str(settings.redis.url), max_connections=settings.redis.max_connections
    )
    await app.state.redis.connect()

    logger.info("application_started")
    try:
        yield
    finally:
        logger.info("application_shutting_down")
        # Teardown in reverse order
        await app.state.redis.close()
        await app.state.kafka.stop()
        await app.state.db.close()
        logger.info("application_shutdown_complete")


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title="LLM Reliability Platform",
        description="Production monitoring and quality assurance for LLM applications",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(ingest.router, prefix="/api/v1", tags=["ingestion"])
    app.include_router(query.router, prefix="/api/v1", tags=["query"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
    app.include_router(invariants.router, prefix="/api/v1", tags=["invariants"])
    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])

    return app


