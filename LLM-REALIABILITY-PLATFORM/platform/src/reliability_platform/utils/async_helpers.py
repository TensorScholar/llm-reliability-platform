 from __future__ import annotations

 import asyncio
 from typing import Awaitable, Iterable, TypeVar


 T = TypeVar("T")


 async def gather_safe(tasks: Iterable[Awaitable[T]]) -> list[T]:
     results = await asyncio.gather(*tasks, return_exceptions=True)
     return [r for r in results if not isinstance(r, Exception)]  # type: ignore[list-item]


