 from __future__ import annotations

 import asyncio
 from dataclasses import dataclass, field
 from typing import Any, Dict, List

 from ..transport.http import HTTPTransport


 @dataclass(slots=True)
 class CaptureBuffer:
     max_size: int
     flush_interval: float
     transport: HTTPTransport
     _buffer: List[Dict[str, Any]] = field(default_factory=list)
     _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

     async def add(self, event: Dict[str, Any]) -> None:
         async with self._lock:
             self._buffer.append(event)
             if len(self._buffer) >= self.max_size:
                 await self._flush_locked()

     async def start_flushing(self) -> None:
         try:
             while True:
                 await asyncio.sleep(self.flush_interval)
                 async with self._lock:
                     await self._flush_locked()
         except asyncio.CancelledError:  # graceful exit
             return

     async def flush(self) -> None:
         async with self._lock:
             await self._flush_locked()

     async def _flush_locked(self) -> None:
         if not self._buffer:
             return
         batch = self._buffer
         self._buffer = []
         # Best-effort send; on failure, drop (non-blocking SDK requirement)
         try:
             if len(batch) == 1:
                 await self.transport.send_capture(batch[0])
             else:
                 await self.transport.send_batch(batch)
         except Exception:
             pass


