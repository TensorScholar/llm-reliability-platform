 from __future__ import annotations

 import time
 from dataclasses import dataclass

 from .redis_client import RedisClient


 @dataclass(slots=True)
 class TokenBucketRateLimiter:
     client: RedisClient
     key_prefix: str = "rate:bucket:"

     async def allow(self, key: str, capacity: int, refill_rate_per_sec: float) -> bool:
         now = int(time.time())
         bucket_key = f"{self.key_prefix}{key}"
         pipe = self.client.client.pipeline()
         # Initialize bucket if not exists
         await pipe.hsetnx(bucket_key, "tokens", capacity)
         await pipe.hsetnx(bucket_key, "ts", now)
         await pipe.hgetall(bucket_key)
         data = await pipe.execute()
         state = data[-1]
         tokens = float(state.get("tokens", capacity))
         last_ts = int(state.get("ts", now))
         # Refill
         delta = max(0, now - last_ts)
         tokens = min(capacity, tokens + delta * refill_rate_per_sec)
         allowed = tokens >= 1.0
         tokens = tokens - 1.0 if allowed else tokens
         await self.client.client.hset(bucket_key, mapping={"tokens": tokens, "ts": now})
         return allowed


