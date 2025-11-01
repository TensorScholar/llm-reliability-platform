 from __future__ import annotations

 import asyncio
 import time
 from typing import Any, Dict, List, Optional
 from uuid import uuid4

 import structlog

 from .capture.buffer import CaptureBuffer
 from .config import SDKConfig
 from .sampling import SamplingStrategy
 from .transport.http import HTTPTransport


 logger = structlog.get_logger()


 class ReliabilityClient:
     def __init__(
         self,
         api_url: str,
         api_key: Optional[str] = None,
         application_name: str = "default",
         config: Optional[SDKConfig] = None,
     ) -> None:
         self.config = config or SDKConfig(
             api_url=api_url,
             api_key=api_key,
             application_name=application_name,
         )
         self.transport = HTTPTransport(
             api_url=self.config.api_url, api_key=self.config.api_key, timeout=self.config.timeout_seconds
         )
         self.buffer = CaptureBuffer(
             max_size=self.config.buffer_max_size,
             flush_interval=self.config.buffer_flush_interval,
             transport=self.transport,
         )
         self.sampling = SamplingStrategy(rate=self.config.sampling_rate, strategy=self.config.sampling_strategy)
         self._background_task: Optional[asyncio.Task] = None
         self._started = False

     async def start(self) -> None:
         if self._started:
             return
         self._started = True
         self._background_task = asyncio.create_task(self.buffer.start_flushing())
         logger.info("sdk_started", application=self.config.application_name)

     async def stop(self) -> None:
         if not self._started:
             return
         self._started = False
         await self.buffer.flush()
         if self._background_task:
             self._background_task.cancel()
             try:
                 await self._background_task
             except asyncio.CancelledError:
                 pass
         await self.transport.close()
         logger.info("sdk_stopped")

     async def capture(
         self,
         prompt: Optional[str] = None,
         messages: Optional[List[Dict[str, str]]] = None,
         response_text: str = "",
         model_provider: str = "openai",
         model_name: str = "gpt-4",
         temperature: float = 0.7,
         tokens_prompt: Optional[int] = None,
         tokens_completion: Optional[int] = None,
         latency_ms: Optional[int] = None,
         user_id: Optional[str] = None,
         session_id: Optional[str] = None,
         custom_metadata: Optional[Dict[str, Any]] = None,
     ) -> bool:
         if not self.sampling.should_capture():
             return False
         event = {
             "request_id": str(uuid4()),
             "request_type": "chat" if messages else "completion",
             "prompt": prompt,
             "messages": messages,
             "model_provider": model_provider,
             "model_name": model_name,
             "temperature": temperature,
             "response_text": response_text,
             "tokens_prompt": tokens_prompt or self._estimate_tokens(prompt or ""),
             "tokens_completion": tokens_completion or self._estimate_tokens(response_text),
             "latency_ms": latency_ms or 0,
             "user_id": user_id,
             "session_id": session_id,
             "application_name": self.config.application_name,
             "custom_metadata": custom_metadata or {},
             "timestamp": time.time(),
         }
         await self.buffer.add(event)
         logger.debug("capture_added", request_id=event["request_id"])
         return True

     def _estimate_tokens(self, text: str) -> int:
         return len(text) // 4

     async def __aenter__(self) -> "ReliabilityClient":
         await self.start()
         return self

     async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
         await self.stop()


