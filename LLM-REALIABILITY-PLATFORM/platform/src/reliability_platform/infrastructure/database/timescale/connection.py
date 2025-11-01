 from __future__ import annotations

 from typing import AsyncGenerator

 from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
 import structlog

 from .models import Base


 logger = structlog.get_logger()


 class TimescaleDB:
     """TimescaleDB connection manager (async SQLAlchemy)."""

     def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10) -> None:
         self.engine = create_async_engine(
             database_url,
             pool_size=pool_size,
             max_overflow=max_overflow,
             pool_pre_ping=True,
             echo=False,
         )
         self.session_factory = async_sessionmaker(
             self.engine,
             class_=AsyncSession,
             expire_on_commit=False,
         )

     async def create_tables(self) -> None:
         async with self.engine.begin() as conn:
             await conn.run_sync(Base.metadata.create_all)
             logger.info("timescale_tables_created")

    async def create_hypertables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                """
                SELECT create_hypertable('capture_events','captured_at', if_not_exists => TRUE);
                """
            )
            await conn.execute(
                """
                SELECT create_hypertable('validation_results','timestamp', if_not_exists => TRUE);
                """
            )
            await conn.execute(
                """
                SELECT create_hypertable('drift_metrics','timestamp', if_not_exists => TRUE);
                """
            )
            logger.info("timescale_hypertables_created")

    async def setup_retention_policies(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                """
                SELECT add_retention_policy('capture_events', INTERVAL '90 days', if_not_exists => TRUE);
                """
            )
            await conn.execute(
                """
                SELECT add_retention_policy('validation_results', INTERVAL '180 days', if_not_exists => TRUE);
                """
            )
            await conn.execute(
                """
                SELECT add_retention_policy('drift_metrics', INTERVAL '365 days', if_not_exists => TRUE);
                """
            )
            logger.info("timescale_retention_policies_created")

    async def setup_continuous_aggregates(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS capture_stats_hourly
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 hour', captured_at) AS bucket,
                    application_name,
                    COUNT(*) as request_count,
                    AVG(latency_ms) as avg_latency_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
                    AVG(tokens_total) as avg_tokens,
                    SUM(cost_usd) as total_cost_usd
                FROM capture_events
                GROUP BY bucket, application_name
                WITH NO DATA;
                """
            )
            await conn.execute(
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS validation_stats_daily
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 day', timestamp) AS bucket,
                    invariant_id,
                    COUNT(*) as total_validations,
                    COUNT(*) FILTER (WHERE status = 'passed') as passed_count,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                    COUNT(*) FILTER (WHERE severity = 'critical') as critical_count
                FROM validation_results
                GROUP BY bucket, invariant_id
                WITH NO DATA;
                """
            )
            logger.info("timescale_continuous_aggregates_created")

     async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
         async with self.session_factory() as session:
             try:
                 yield session
             except Exception:  # noqa: BLE001
                 await session.rollback()
                 raise
             finally:
                 await session.close()

     async def close(self) -> None:
         await self.engine.dispose()
         logger.info("timescale_connection_closed")


