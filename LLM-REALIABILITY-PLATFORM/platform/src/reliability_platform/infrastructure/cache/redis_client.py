 from __future__ import annotations

 from dataclasses import dataclass
 from typing import Optional

 from redis.asyncio import Redis


 @dataclass(slots=True)
 class RedisClient:
     redis_url: str
     max_connections: int = 50
     _client: Optional[Redis] = None

     async def connect(self) -> None:
         if self._client is None:
             self._client = Redis.from_url(self.redis_url, max_connections=self.max_connections, encoding="utf-8", decode_responses=True)

     async def close(self) -> None:
         if self._client is not None:
             await self._client.close()
             self._client = None

     @property
     def client(self) -> Redis:
         if self._client is None:
             raise RuntimeError("Redis client not connected")
         return self._client


