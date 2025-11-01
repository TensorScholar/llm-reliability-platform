 from __future__ import annotations

 from datetime import datetime
 from typing import Any, Dict, List, Optional

 import structlog
 from fastapi import APIRouter, Depends, HTTPException
 from pydantic import BaseModel

 from ....infrastructure.messaging.kafka_producer import KafkaProducerClient
 from ....infrastructure.messaging.topics import KafkaTopics
 from ..dependencies import get_kafka_producer


 router = APIRouter()
 logger = structlog.get_logger()


 class IngestRequest(BaseModel):
     request_id: str
     request_type: str = "chat"
     prompt: Optional[str] = None
     messages: Optional[List[Dict[str, str]]] = None
     model_provider: str
     model_name: str
     temperature: float = 0.7
     response_text: str
     finish_reason: Optional[str] = None
     tokens_prompt: Optional[int] = None
     tokens_completion: Optional[int] = None
     latency_ms: int
     user_id: Optional[str] = None
     session_id: Optional[str] = None
     application_name: str = "default"
     ab_variant: Optional[str] = None
     custom_metadata: Optional[Dict[str, Any]] = None
     timestamp: Optional[datetime] = None


 class IngestResponse(BaseModel):
     success: bool
     capture_id: str
     message: str


 @router.post("/captures", response_model=IngestResponse)
 async def ingest_capture(
     request: IngestRequest,
     kafka: KafkaProducerClient = Depends(get_kafka_producer),
 ) -> IngestResponse:
     try:
         payload = request.model_dump()
         payload["id"] = request.request_id
         if not await kafka.send(KafkaTopics.CAPTURES_RAW, value=payload, key=request.application_name):
             raise HTTPException(status_code=500, detail="Failed to publish capture event")
         logger.info("capture_ingested", capture_id=request.request_id, application=request.application_name)
         return IngestResponse(success=True, capture_id=request.request_id, message="Capture ingested")
     except Exception as e:  # noqa: BLE001
         logger.error("ingestion_error", error=str(e))
         raise HTTPException(status_code=500, detail=str(e))


@router.post("/captures/batch")
async def ingest_batch(
    requests: List[IngestRequest], kafka: KafkaProducerClient = Depends(get_kafka_producer)
) -> Dict[str, Any]:
    if len(requests) > 1000:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 1000 events")
    success, failed, ids = 0, 0, []
    for r in requests:
        try:
            payload = r.model_dump()
            payload["id"] = r.request_id
            ok = await kafka.send(KafkaTopics.CAPTURES_RAW, value=payload, key=r.application_name)
            if ok:
                success += 1
                ids.append(r.request_id)
            else:
                failed += 1
        except Exception:
            failed += 1
    return {"success": True, "total": len(requests), "succeeded": success, "failed": failed, "capture_ids": ids}


