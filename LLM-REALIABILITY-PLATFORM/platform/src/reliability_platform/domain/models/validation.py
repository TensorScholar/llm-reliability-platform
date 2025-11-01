 from __future__ import annotations

 from dataclasses import dataclass, field
 from datetime import datetime
 from enum import Enum
 from typing import Any, Dict, List, Optional
 from uuid import UUID, uuid4


 class Severity(str, Enum):
     """Severity levels for validation failures."""

     CRITICAL = "critical"
     HIGH = "high"
     MEDIUM = "medium"
     LOW = "low"
     INFO = "info"


 class ValidationStatus(str, Enum):
     """Status of validation execution."""

     PASSED = "passed"
     FAILED = "failed"
     SKIPPED = "skipped"
     ERROR = "error"


 @dataclass(frozen=True)
 class ValidationEvidence:
     """Evidence supporting a validation result."""

     description: str
     extracted_text: Optional[str] = None
     confidence_score: Optional[float] = None
     metadata: Dict[str, Any] = field(default_factory=dict)

     def __post_init__(self) -> None:
         if self.confidence_score is not None and not 0 <= self.confidence_score <= 1:
             raise ValueError("Confidence score must be between 0 and 1")


 @dataclass(frozen=True)
 class ValidationResult:
     """Result of a single invariant validation."""

     id: UUID = field(default_factory=uuid4)
     invariant_id: str = ""
     capture_event_id: UUID = field(default_factory=uuid4)
     status: ValidationStatus = ValidationStatus.PASSED
     severity: Severity = Severity.MEDIUM
     message: str = ""
     evidence: List[ValidationEvidence] = field(default_factory=list)
     execution_time_ms: int = 0
     timestamp: datetime = field(default_factory=datetime.utcnow)

     @property
     def passed(self) -> bool:
         """Check if validation passed."""

         return self.status == ValidationStatus.PASSED

     @property
     def requires_action(self) -> bool:
         """Check if result requires immediate action."""

         return self.status == ValidationStatus.FAILED and self.severity in {
             Severity.CRITICAL,
             Severity.HIGH,
         }

     def to_dict(self) -> Dict[str, Any]:
         """Serialize to dictionary."""

         return {
             "id": str(self.id),
             "invariant_id": self.invariant_id,
             "capture_event_id": str(self.capture_event_id),
             "status": self.status.value,
             "severity": self.severity.value,
             "message": self.message,
             "evidence": [
                 {
                     "description": e.description,
                     "extracted_text": e.extracted_text,
                     "confidence_score": e.confidence_score,
                     "metadata": e.metadata,
                 }
                 for e in self.evidence
             ],
             "execution_time_ms": self.execution_time_ms,
             "timestamp": self.timestamp.isoformat(),
         }


 @dataclass(frozen=True)
 class BatchValidationResult:
     """Results from validating multiple captures."""

     id: UUID = field(default_factory=uuid4)
     results: List[ValidationResult] = field(default_factory=list)
     total_validations: int = 0
     passed_count: int = 0
     failed_count: int = 0
     error_count: int = 0
     total_execution_time_ms: int = 0
     timestamp: datetime = field(default_factory=datetime.utcnow)

     @property
     def pass_rate(self) -> float:
         """Calculate pass rate."""

         if self.total_validations == 0:
             return 0.0
         return self.passed_count / self.total_validations

     @property
     def critical_failures(self) -> List[ValidationResult]:
         """Get all critical failures."""

         return [
             r
             for r in self.results
             if r.status == ValidationStatus.FAILED and r.severity == Severity.CRITICAL
         ]


