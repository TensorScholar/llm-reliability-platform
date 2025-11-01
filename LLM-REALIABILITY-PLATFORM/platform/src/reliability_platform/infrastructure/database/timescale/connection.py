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


