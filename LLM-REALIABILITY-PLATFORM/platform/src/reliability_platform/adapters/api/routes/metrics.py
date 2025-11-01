 from __future__ import annotations

 from fastapi import APIRouter, Response
 from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest


 router = APIRouter()


 @router.get("/metrics")
 async def metrics() -> Response:
     registry = CollectorRegistry()  # default is fine; extend in future
     data = generate_latest(registry)
     return Response(content=data, media_type=CONTENT_TYPE_LATEST)


