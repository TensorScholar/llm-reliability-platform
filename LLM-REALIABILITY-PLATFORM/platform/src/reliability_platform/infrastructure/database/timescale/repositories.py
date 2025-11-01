 from __future__ import annotations

 from datetime import datetime
 from typing import List, Optional
 from uuid import UUID

 from sqlalchemy import and_, func, select
 from sqlalchemy.ext.asyncio import AsyncSession
 import structlog

 from .models import CaptureEventModel, ValidationResultModel, DriftMetricModel
 from ....domain.models.capture import CaptureEvent
 from ....domain.models.validation import ValidationResult
 from ....domain.models.drift import DriftMetric


 logger = structlog.get_logger()


 class CaptureRepository:
     def __init__(self, session: AsyncSession) -> None:
         self.session = session

     async def save(self, capture: CaptureEvent) -> None:
         model = CaptureEventModel(
             id=capture.id,
             captured_at=capture.captured_at,
             request_id=capture.request.id,
             request_type=capture.request.request_type.value,
             prompt=capture.request.prompt,
             messages=capture.request.messages,
             model_provider=capture.request.model_config.provider.value,
             model_name=capture.request.model_config.model_name,
             temperature=capture.request.model_config.temperature,
             user_id=capture.request.context.user_id,
             session_id=capture.request.context.session_id,
             application_name=capture.request.context.application_name,
             ab_variant=capture.request.context.ab_variant,
             environment=capture.request.context.environment,
             custom_metadata=capture.request.context.custom_metadata,
             response_id=capture.response.id,
             response_text=capture.response.text,
             finish_reason=capture.response.finish_reason,
             tokens_prompt=capture.response.usage.get("tokens_prompt"),
             tokens_completion=capture.response.usage.get("tokens_completion"),
             tokens_total=capture.response.total_tokens,
             latency_ms=capture.response.latency_ms,
             cost_usd=capture.response.cost_usd,
             sdk_version=capture.sdk_version,
         )
         self.session.add(model)
         await self.session.commit()

     async def get_by_id(self, capture_id: UUID) -> Optional[CaptureEventModel]:
         result = await self.session.execute(
             select(CaptureEventModel).where(CaptureEventModel.id == capture_id)
         )
         return result.scalar_one_or_none()

     async def get_captures_in_window(
         self,
         application_name: str,
         start: datetime,
         end: datetime,
         limit: int = 10000,
     ) -> List[CaptureEventModel]:
         result = await self.session.execute(
             select(CaptureEventModel)
             .where(
                 and_(
                     CaptureEventModel.application_name == application_name,
                     CaptureEventModel.captured_at >= start,
                     CaptureEventModel.captured_at <= end,
                 )
             )
             .order_by(CaptureEventModel.captured_at.desc())
             .limit(limit)
         )
         return list(result.scalars().all())

     async def get_stats_for_period(
         self, application_name: str, start: datetime, end: datetime
     ) -> dict:
         result = await self.session.execute(
             select(
                 func.count(CaptureEventModel.id).label("total_requests"),
                 func.avg(CaptureEventModel.latency_ms).label("avg_latency_ms"),
                 func.percentile_cont(0.95).within_group(CaptureEventModel.latency_ms).label(
                     "p95_latency_ms"
                 ),
                 func.sum(CaptureEventModel.cost_usd).label("total_cost_usd"),
             ).where(
                 and_(
                     CaptureEventModel.application_name == application_name,
                     CaptureEventModel.captured_at >= start,
                     CaptureEventModel.captured_at <= end,
                 )
             )
         )
         row = result.first()
         return {
             "total_requests": (row.total_requests or 0) if row else 0,
             "avg_latency_ms": float(row.avg_latency_ms) if row and row.avg_latency_ms else 0.0,
             "p95_latency_ms": float(row.p95_latency_ms) if row and row.p95_latency_ms else 0.0,
             "total_cost_usd": float(row.total_cost_usd) if row and row.total_cost_usd else 0.0,
         }


 class ValidationResultRepository:
     def __init__(self, session: AsyncSession) -> None:
         self.session = session

     async def save(self, result: ValidationResult) -> None:
         model = ValidationResultModel(
             id=result.id,
             capture_event_id=result.capture_event_id,
             invariant_id=result.invariant_id,
             status=result.status,
             severity=result.severity,
             message=result.message,
             evidence=[e.__dict__ for e in result.evidence],
             execution_time_ms=result.execution_time_ms,
             timestamp=result.timestamp,
         )
         self.session.add(model)
         await self.session.commit()

     async def save_batch(self, results: List[ValidationResult]) -> None:
         models = [
             ValidationResultModel(
                 id=r.id,
                 capture_event_id=r.capture_event_id,
                 invariant_id=r.invariant_id,
                 status=r.status,
                 severity=r.severity,
                 message=r.message,
                 evidence=[e.__dict__ for e in r.evidence],
                 execution_time_ms=r.execution_time_ms,
                 timestamp=r.timestamp,
             )
             for r in results
         ]
         self.session.add_all(models)
         await self.session.commit()


 class DriftMetricRepository:
     def __init__(self, session: AsyncSession) -> None:
         self.session = session

     async def save(self, metric: DriftMetric) -> None:
         model = DriftMetricModel(
             id=metric.id,
             drift_type=metric.drift_type.value,
             metric_name=metric.metric_name,
             value=metric.value,
             threshold=metric.threshold,
             severity=metric.severity.value,
             application_name=metric.metadata.get("application_name", "unknown"),
             baseline_window_start=metric.baseline_window.start,
             baseline_window_end=metric.baseline_window.end,
             comparison_window_start=metric.comparison_window.start,
             comparison_window_end=metric.comparison_window.end,
             metadata=metric.metadata,
             timestamp=metric.timestamp,
         )
         self.session.add(model)
         await self.session.commit()

     async def save_batch(self, metrics: List[DriftMetric]) -> None:
         models = [
             DriftMetricModel(
                 id=m.id,
                 drift_type=m.drift_type.value,
                 metric_name=m.metric_name,
                 value=m.value,
                 threshold=m.threshold,
                 severity=m.severity.value,
                 application_name=m.metadata.get("application_name", "unknown"),
                 baseline_window_start=m.baseline_window.start,
                 baseline_window_end=m.baseline_window.end,
                 comparison_window_start=m.comparison_window.start,
                 comparison_window_end=m.comparison_window.end,
                 metadata=m.metadata,
                 timestamp=m.timestamp,
             )
             for m in metrics
         ]
         self.session.add_all(models)
         await self.session.commit()


