 from __future__ import annotations

 from sqlalchemy import (
     Column,
     String,
     Integer,
     Float,
     JSON,
     Text,
     DateTime,
     Index,
     ForeignKey,
     Enum as SQLEnum,
 )
 from sqlalchemy.dialects.postgresql import UUID as PGUUID
 from sqlalchemy.orm import declarative_base
 from sqlalchemy.sql import func
 import uuid as uuid_lib

 from ....domain.models.validation import ValidationStatus, Severity


 Base = declarative_base()


 class CaptureEventModel(Base):
     __tablename__ = "capture_events"

     id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
     captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
     created_at = Column(DateTime(timezone=True), server_default=func.now())

     request_id = Column(PGUUID(as_uuid=True), nullable=False)
     request_type = Column(String(50), nullable=False)
     prompt = Column(Text)
     messages = Column(JSON)

     model_provider = Column(String(50), nullable=False)
     model_name = Column(String(100), nullable=False)
     temperature = Column(Float)

     user_id = Column(String(255), index=True)
     session_id = Column(String(255), index=True)
     application_name = Column(String(100), nullable=False, index=True)
     ab_variant = Column(String(50))
     environment = Column(String(50), default="production")
     custom_metadata = Column(JSON)

     response_id = Column(PGUUID(as_uuid=True), nullable=False)
     response_text = Column(Text, nullable=False)
     finish_reason = Column(String(50))

     tokens_prompt = Column(Integer)
     tokens_completion = Column(Integer)
     tokens_total = Column(Integer)
     latency_ms = Column(Integer)
     cost_usd = Column(Float)

     sdk_version = Column(String(20))

     __table_args__ = (
         Index("idx_app_timestamp", "application_name", "captured_at"),
         Index("idx_user_timestamp", "user_id", "captured_at"),
         Index("idx_session_timestamp", "session_id", "captured_at"),
     )


 class ValidationResultModel(Base):
     __tablename__ = "validation_results"

     id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
     capture_event_id = Column(
         PGUUID(as_uuid=True),
         ForeignKey("capture_events.id", ondelete="CASCADE"),
         nullable=False,
         index=True,
     )
     invariant_id = Column(String(100), nullable=False, index=True)
     status = Column(SQLEnum(ValidationStatus), nullable=False, index=True)
     severity = Column(SQLEnum(Severity), nullable=False, index=True)
     message = Column(Text, nullable=False)
     evidence = Column(JSON)
     execution_time_ms = Column(Integer)
     timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
     created_at = Column(DateTime(timezone=True), server_default=func.now())

     __table_args__ = (
         Index("idx_invariant_timestamp", "invariant_id", "timestamp"),
         Index("idx_status_severity", "status", "severity"),
     )


 class DriftMetricModel(Base):
     __tablename__ = "drift_metrics"

     id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
     drift_type = Column(String(50), nullable=False, index=True)
     metric_name = Column(String(100), nullable=False, index=True)
     value = Column(Float, nullable=False)
     threshold = Column(Float, nullable=False)
     severity = Column(String(20), nullable=False, index=True)
     application_name = Column(String(100), nullable=False, index=True)
     baseline_window_start = Column(DateTime(timezone=True), nullable=False)
     baseline_window_end = Column(DateTime(timezone=True), nullable=False)
     comparison_window_start = Column(DateTime(timezone=True), nullable=False)
     comparison_window_end = Column(DateTime(timezone=True), nullable=False)
     metadata = Column(JSON)
     timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
     created_at = Column(DateTime(timezone=True), server_default=func.now())

     __table_args__ = (
         Index(
             "idx_app_metric_timestamp",
             "application_name",
             "metric_name",
             "timestamp",
         ),
     )


