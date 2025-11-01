 from __future__ import annotations

 import json
 import time
 from typing import Callable

 import structlog
 from fastapi import Request, Response
 from starlette.middleware.base import BaseHTTPMiddleware


 logger = structlog.get_logger()


 class RequestLoggingMiddleware(BaseHTTPMiddleware):
     async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
         start = time.time()
         response: Response
         try:
             response = await call_next(request)
         finally:
             duration_ms = int((time.time() - start) * 1000)
             logger.info(
                 "http_request",
                 method=request.method,
                 path=request.url.path,
                 status=getattr(response, "status_code", 0),
                 duration_ms=duration_ms,
             )
         return response


 class ErrorHandlingMiddleware(BaseHTTPMiddleware):
     async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
         try:
             return await call_next(request)
         except Exception as e:  # noqa: BLE001
             logger.error("unhandled_exception", path=request.url.path, error=str(e))
             return Response(
                 content=json.dumps({"detail": "Internal Server Error"}),
                 status_code=500,
                 media_type="application/json",
             )


