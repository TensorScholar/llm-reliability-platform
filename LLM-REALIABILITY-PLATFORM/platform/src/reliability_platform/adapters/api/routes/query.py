 from __future__ import annotations

 from datetime import datetime, timedelta
 from typing import List, Optional
 from uuid import UUID

 from fastapi import APIRouter, Depends, HTTPException, Query
 from pydantic import BaseModel

 from ....infrastructure.database.timescale.repositories import CaptureRepository
 from ..dependencies import get_db_session


 router = APIRouter()


 class CaptureQueryResponse(BaseModel):
     id: str
     application_name: str
     user_id: Optional[str]
     prompt: Optional[str]
     response_text: str
     latency_ms: int
     cost_usd: float
     captured_at: datetime


 @router.get("/captures", response_model=List[CaptureQueryResponse])
 async def query_captures(
     application_name: str,
     start_time: Optional[datetime] = Query(None),
     end_time: Optional[datetime] = Query(None),
     user_id: Optional[str] = None,
     limit: int = Query(100, le=1000),
     db_session=Depends(get_db_session),
 ) -> List[CaptureQueryResponse]:
     if not start_time:
         start_time = datetime.utcnow() - timedelta(hours=24)
     if not end_time:
         end_time = datetime.utcnow()

     repo = CaptureRepository(db_session)
     captures = await repo.get_captures_in_window(
         application_name=application_name, start=start_time, end=end_time, limit=limit
     )
     if user_id:
         captures = [c for c in captures if c.user_id == user_id]
     return [
         CaptureQueryResponse(
             id=str(c.id),
             application_name=c.application_name,
             user_id=c.user_id,
             prompt=c.prompt,
             response_text=c.response_text,
             latency_ms=c.latency_ms or 0,
             cost_usd=c.cost_usd or 0.0,
             captured_at=c.captured_at,
         )
         for c in captures
     ]


 @router.get("/captures/{capture_id}")
 async def get_capture_by_id(capture_id: UUID, db_session=Depends(get_db_session)):
     repo = CaptureRepository(db_session)
     c = await repo.get_by_id(capture_id)
     if not c:
         raise HTTPException(status_code=404, detail="Capture not found")
     return {
         "id": str(c.id),
         "request": {
             "type": c.request_type,
             "prompt": c.prompt,
             "messages": c.messages,
             "model": {
                 "provider": c.model_provider,
                 "name": c.model_name,
                 "temperature": c.temperature,
             },
         },
         "response": {
             "text": c.response_text,
             "finish_reason": c.finish_reason,
             "tokens_total": c.tokens_total,
             "latency_ms": c.latency_ms,
             "cost_usd": c.cost_usd,
         },
         "context": {
             "user_id": c.user_id,
             "session_id": c.session_id,
             "application_name": c.application_name,
             "ab_variant": c.ab_variant,
         },
         "captured_at": c.captured_at.isoformat(),
     }


 @router.get("/stats/{application_name}")
 async def get_application_stats(
     application_name: str,
     start_time: Optional[datetime] = Query(None),
     end_time: Optional[datetime] = Query(None),
     db_session=Depends(get_db_session),
 ):
     if not start_time:
         start_time = datetime.utcnow() - timedelta(hours=24)
     if not end_time:
         end_time = datetime.utcnow()
     repo = CaptureRepository(db_session)
     stats = await repo.get_stats_for_period(
         application_name=application_name, start=start_time, end=end_time
     )
     return {
         "application_name": application_name,
         "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
         "stats": stats,
     }


