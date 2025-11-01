 from __future__ import annotations

 from abc import ABC, abstractmethod
 from dataclasses import dataclass, field
 from datetime import datetime
 from enum import Enum
 from typing import Any, Dict, List, Optional, Set
 from uuid import UUID, uuid4

 from .capture import CaptureEvent
 from .validation import ValidationResult, ValidationStatus, Severity


 class InvariantCategory(str, Enum):
     """Categories of invariants."""

     SAFETY = "safety"
     FACTUALITY = "factuality"
     COMPLIANCE = "compliance"
     PERFORMANCE = "performance"
     CONSISTENCY = "consistency"
     CUSTOM = "custom"


 class InvariantScope(str, Enum):
     """Scope of invariant application."""

     ALL_REQUESTS = "all_requests"
     SPECIFIC_USERS = "specific_users"
     SPECIFIC_APPLICATIONS = "specific_applications"
     AB_VARIANT = "ab_variant"
     SAMPLE_BASED = "sample_based"


 @dataclass(frozen=True)
 class InvariantConfig:
     """Configuration for an invariant rule."""

     enabled: bool = True
     severity: Severity = Severity.MEDIUM
     scope: InvariantScope = InvariantScope.ALL_REQUESTS
     scope_filters: Dict[str, Any] = field(default_factory=dict)
     sampling_rate: float = 1.0
     timeout_ms: int = 5000
     retry_on_error: bool = True
     max_retries: int = 2
     custom_params: Dict[str, Any] = field(default_factory=dict)

     def __post_init__(self) -> None:
         if not 0 < self.sampling_rate <= 1:
             raise ValueError("Sampling rate must be between 0 and 1")


 @dataclass
 class InvariantMetadata:
     """Metadata about an invariant."""

     id: str
     name: str
     description: str
     category: InvariantCategory
     version: str = "1.0.0"
     author: str = "system"
     tags: Set[str] = field(default_factory=set)
     created_at: datetime = field(default_factory=datetime.utcnow)
     updated_at: datetime = field(default_factory=datetime.utcnow)


 @dataclass
 class InvariantContext:
     """Context provided to invariant execution."""

     capture_event: CaptureEvent
     execution_id: UUID = field(default_factory=uuid4)
     metadata: Dict[str, Any] = field(default_factory=dict)

     @property
     def request(self):
         return self.capture_event.request

     @property
     def response(self):
         return self.capture_event.response


 class AbstractInvariant(ABC):
     """Base class for all invariant rules."""

     def __init__(self, config: InvariantConfig):
         self.config = config
         self._metadata: Optional[InvariantMetadata] = None

     @property
     @abstractmethod
     def metadata(self) -> InvariantMetadata:
         """Return metadata about this invariant."""

     @abstractmethod
     async def validate(self, context: InvariantContext) -> ValidationResult:
         """Execute the invariant validation and return a ValidationResult."""

     def should_apply(self, context: InvariantContext) -> bool:
         """Determine if this invariant should be applied to the given context."""

         if not self.config.enabled:
             return False

         # Scope checks
         if self.config.scope == InvariantScope.SPECIFIC_APPLICATIONS:
             allowed_apps = self.config.scope_filters.get("applications", [])
             if context.request.context.application_name not in allowed_apps:
                 return False

         elif self.config.scope == InvariantScope.SPECIFIC_USERS:
             allowed_users = self.config.scope_filters.get("user_ids", [])
             if context.request.context.user_id not in allowed_users:
                 return False

         elif self.config.scope == InvariantScope.AB_VARIANT:
             required_variant = self.config.scope_filters.get("variant")
             if context.request.context.ab_variant != required_variant:
                 return False

         # Deterministic sampling by request ID
         if self.config.sampling_rate < 1.0:
             import hashlib

             request_hash = int(
                 hashlib.md5(str(context.request.id).encode("utf-8")).hexdigest(), 16
             )
             if (request_hash % 100) / 100.0 > self.config.sampling_rate:
                 return False

         return True

     def _create_result(
         self,
         context: InvariantContext,
         status: ValidationStatus,
         message: str,
         evidence: Optional[List] = None,
         execution_time_ms: int = 0,
     ) -> ValidationResult:
         """Helper to create ValidationResult with shared attributes."""

         return ValidationResult(
             invariant_id=self.metadata.id,
             capture_event_id=context.capture_event.id,
             status=status,
             severity=self.config.severity,
             message=message,
             evidence=evidence or [],
             execution_time_ms=execution_time_ms,
         )


 @dataclass
 class InvariantRegistry:
     """Registry for managing invariant rules (simple plugin system)."""

     _invariants: Dict[str, AbstractInvariant] = field(default_factory=dict)

     def register(self, invariant: AbstractInvariant) -> None:
         invariant_id = invariant.metadata.id
         if invariant_id in self._invariants:
             raise ValueError(f"Invariant {invariant_id} already registered")
         self._invariants[invariant_id] = invariant

     def unregister(self, invariant_id: str) -> None:
         if invariant_id in self._invariants:
             del self._invariants[invariant_id]

     def get(self, invariant_id: str) -> Optional[AbstractInvariant]:
         return self._invariants.get(invariant_id)

     def get_by_category(self, category: InvariantCategory) -> List[AbstractInvariant]:
         return [inv for inv in self._invariants.values() if inv.metadata.category == category]

     def get_all(self) -> List[AbstractInvariant]:
         return list(self._invariants.values())

     def get_enabled(self) -> List[AbstractInvariant]:
         return [inv for inv in self._invariants.values() if inv.config.enabled]


