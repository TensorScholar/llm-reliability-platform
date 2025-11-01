 from __future__ import annotations

 from typing import Any, Optional

 from .redis_client import RedisClient


 class CacheManager:
     def __init__(self, client: RedisClient) -> None:
         self._client = client

     async def get(self, key: str) -> Optional[str]:
         return await self._client.client.get(key)

     async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
         await self._client.client.set(key, value, ex=ttl_seconds)

     async def delete(self, key: str) -> None:
         await self._client.client.delete(key)


