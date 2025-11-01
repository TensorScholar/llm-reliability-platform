 from __future__ import annotations

 from typing import AsyncGenerator

 from fastapi import Depends
 from fastapi import Request

 from ...config import Settings
 from ...infrastructure.database.timescale.connection import TimescaleDB
 from ...infrastructure.messaging.kafka_producer import KafkaProducerClient
from ...infrastructure.cache.redis_client import RedisClient


 def get_settings(request: Request) -> Settings:
     return request.app.state.settings


 async def get_db_session(request: Request):
     db: TimescaleDB = request.app.state.db
     async for session in db.get_session():
         yield session


 def get_kafka_producer(request: Request) -> KafkaProducerClient:
     return request.app.state.kafka


def get_redis_client(request: Request) -> RedisClient:
    return request.app.state.redis


