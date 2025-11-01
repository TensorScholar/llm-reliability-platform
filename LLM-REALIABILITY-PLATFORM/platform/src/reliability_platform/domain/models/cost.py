 from __future__ import annotations

 from dataclasses import dataclass, field
 from datetime import datetime
 from enum import Enum
 from typing import Any, Dict, List
 from uuid import UUID, uuid4


 class CostCategory(str, Enum):
     """Categories of costs."""

     INFRASTRUCTURE = "infrastructure"
     OPERATIONAL = "operational"
     BUSINESS = "business"
     REGULATORY = "regulatory"
     REPUTATIONAL = "reputational"


 class ImpactLevel(str, Enum):
     """Level of business impact."""

     NEGLIGIBLE = "negligible"
     LOW = "low"
     MEDIUM = "medium"
     HIGH = "high"
     CRITICAL = "critical"


 @dataclass(frozen=True)
 class CostBreakdown:
     """Detailed cost breakdown."""

     infrastructure_usd: float = 0.0
     operational_usd: float = 0.0
     business_usd: float = 0.0
     regulatory_usd: float = 0.0
     reputational_usd: float = 0.0

     @property
     def total_usd(self) -> float:
         return (
             self.infrastructure_usd
             + self.operational_usd
             + self.business_usd
             + self.regulatory_usd
             + self.reputational_usd
         )

     def to_dict(self) -> Dict[str, float]:
         return {
             "infrastructure_usd": self.infrastructure_usd,
             "operational_usd": self.operational_usd,
             "business_usd": self.business_usd,
             "regulatory_usd": self.regulatory_usd,
             "reputational_usd": self.reputational_usd,
             "total_usd": self.total_usd,
         }


 @dataclass(frozen=True)
 class CostImpact:
     """Cost impact of a quality issue."""

     id: UUID = field(default_factory=uuid4)
     related_event_id: UUID = field(default_factory=uuid4)
     impact_level: ImpactLevel = ImpactLevel.LOW
     cost_breakdown: CostBreakdown = field(default_factory=CostBreakdown)
     description: str = ""
     calculation_method: str = ""
     confidence_score: float = 0.5
     timestamp: datetime = field(default_factory=datetime.utcnow)
     metadata: Dict[str, Any] = field(default_factory=dict)

     def __post_init__(self) -> None:
         if not 0 <= self.confidence_score <= 1:
             raise ValueError("Confidence score must be between 0 and 1")

     @property
     def total_cost_usd(self) -> float:
         return self.cost_breakdown.total_usd

     def to_dict(self) -> Dict[str, Any]:
         return {
             "id": str(self.id),
             "related_event_id": str(self.related_event_id),
             "impact_level": self.impact_level.value,
             "cost_breakdown": self.cost_breakdown.to_dict(),
             "description": self.description,
             "calculation_method": self.calculation_method,
             "confidence_score": self.confidence_score,
             "timestamp": self.timestamp.isoformat(),
             "metadata": self.metadata,
         }


 @dataclass
 class CostAggregation:
     """Aggregated cost metrics over a period."""

     period_start: datetime
     period_end: datetime
     total_events: int
     total_failures: int
     total_cost_usd: float
     cost_by_category: Dict[CostCategory, float]
     cost_by_severity: Dict[str, float]
     top_cost_drivers: List[Dict[str, Any]]

     @property
     def average_cost_per_event(self) -> float:
         if self.total_events == 0:
             return 0.0
         return self.total_cost_usd / self.total_events

     @property
     def average_cost_per_failure(self) -> float:
         if self.total_failures == 0:
             return 0.0
         return self.total_cost_usd / self.total_failures

     def to_dict(self) -> Dict[str, Any]:
         return {
             "period_start": self.period_start.isoformat(),
             "period_end": self.period_end.isoformat(),
             "total_events": self.total_events,
             "total_failures": self.total_failures,
             "total_cost_usd": self.total_cost_usd,
             "average_cost_per_event": self.average_cost_per_event,
             "average_cost_per_failure": self.average_cost_per_failure,
             "cost_by_category": {k.value: v for k, v in self.cost_by_category.items()},
             "cost_by_severity": self.cost_by_severity,
             "top_cost_drivers": self.top_cost_drivers,
         }


