 from __future__ import annotations

 from dataclasses import dataclass, field
 from datetime import datetime, timedelta
 from enum import Enum
 from typing import Any, Dict, List, Optional
 from uuid import UUID, uuid4

 import numpy as np


 class DriftType(str, Enum):
     """Types of drift detection."""

     STATISTICAL = "statistical"
     SEMANTIC = "semantic"
     BEHAVIORAL = "behavioral"
     PERFORMANCE = "performance"


 class DriftSeverity(str, Enum):
     """Severity of detected drift."""

     NONE = "none"
     LOW = "low"
     MEDIUM = "medium"
     HIGH = "high"
     CRITICAL = "critical"


 @dataclass(frozen=True)
 class DriftWindow:
     """Time window for drift comparison."""

     start: datetime
     end: datetime
     label: str

     @property
     def duration(self) -> timedelta:
         return self.end - self.start

     def contains(self, timestamp: datetime) -> bool:
         return self.start <= timestamp <= self.end


 @dataclass
 class DistributionMetrics:
     """Statistical metrics for a distribution."""

     mean: float
     median: float
     std_dev: float
     min_value: float
     max_value: float
     percentile_95: float
     percentile_99: float
     sample_count: int

     @classmethod
     def from_samples(cls, samples: List[float]) -> "DistributionMetrics":
         if not samples:
             raise ValueError("Cannot calculate metrics from empty samples")
         arr = np.array(samples)
         return cls(
             mean=float(np.mean(arr)),
             median=float(np.median(arr)),
             std_dev=float(np.std(arr)),
             min_value=float(np.min(arr)),
             max_value=float(np.max(arr)),
             percentile_95=float(np.percentile(arr, 95)),
             percentile_99=float(np.percentile(arr, 99)),
             sample_count=len(samples),
         )


 @dataclass(frozen=True)
 class DriftMetric:
     """A single drift metric measurement."""

     id: UUID = field(default_factory=uuid4)
     drift_type: DriftType = DriftType.STATISTICAL
     metric_name: str = ""
     value: float = 0.0
     threshold: float = 0.0
     severity: DriftSeverity = DriftSeverity.NONE
     baseline_window: DriftWindow = field(default_factory=lambda: DriftWindow(datetime.utcnow(), datetime.utcnow(), "baseline"))
     comparison_window: DriftWindow = field(default_factory=lambda: DriftWindow(datetime.utcnow(), datetime.utcnow(), "current"))
     timestamp: datetime = field(default_factory=datetime.utcnow)
     metadata: Dict[str, Any] = field(default_factory=dict)

     @property
     def is_drifting(self) -> bool:
         return self.value > self.threshold

     @property
     def drift_ratio(self) -> float:
         if self.threshold == 0:
             return float("inf") if self.value > 0 else 0.0
         return self.value / self.threshold

     def to_dict(self) -> Dict[str, Any]:
         return {
             "id": str(self.id),
             "drift_type": self.drift_type.value,
             "metric_name": self.metric_name,
             "value": self.value,
             "threshold": self.threshold,
             "severity": self.severity.value,
             "is_drifting": self.is_drifting,
             "drift_ratio": self.drift_ratio,
             "baseline_window": {
                 "start": self.baseline_window.start.isoformat(),
                 "end": self.baseline_window.end.isoformat(),
                 "label": self.baseline_window.label,
             },
             "comparison_window": {
                 "start": self.comparison_window.start.isoformat(),
                 "end": self.comparison_window.end.isoformat(),
                 "label": self.comparison_window.label,
             },
             "timestamp": self.timestamp.isoformat(),
             "metadata": self.metadata,
         }


 @dataclass(frozen=True)
 class DriftAlert:
     """Alert triggered by drift detection."""

     id: UUID = field(default_factory=uuid4)
     drift_metrics: List[DriftMetric] = field(default_factory=list)
     overall_severity: DriftSeverity = DriftSeverity.LOW
     title: str = ""
     description: str = ""
     recommended_actions: List[str] = field(default_factory=list)
     affected_scope: Dict[str, Any] = field(default_factory=dict)
     timestamp: datetime = field(default_factory=datetime.utcnow)
     acknowledged: bool = False
     resolved: bool = False

     @property
     def is_critical(self) -> bool:
         return self.overall_severity in {DriftSeverity.HIGH, DriftSeverity.CRITICAL}

     @property
     def drift_count(self) -> int:
         return sum(1 for m in self.drift_metrics if m.is_drifting)

     def to_dict(self) -> Dict[str, Any]:
         return {
             "id": str(self.id),
             "drift_metrics": [m.to_dict() for m in self.drift_metrics],
             "overall_severity": self.overall_severity.value,
             "title": self.title,
             "description": self.description,
             "recommended_actions": self.recommended_actions,
             "affected_scope": self.affected_scope,
             "timestamp": self.timestamp.isoformat(),
             "acknowledged": self.acknowledged,
             "resolved": self.resolved,
             "is_critical": self.is_critical,
             "drift_count": self.drift_count,
         }


 @dataclass
 class DriftDetectionConfig:
     """Configuration for drift detection."""

     enabled: bool = True
     detection_interval_minutes: int = 15
     baseline_window_hours: int = 24
     comparison_window_hours: int = 1
     min_samples_required: int = 100
     kl_divergence_threshold: float = 0.1
     js_divergence_threshold: float = 0.1
     cosine_distance_threshold: float = 0.15
     response_length_change_threshold: float = 0.3
     latency_change_threshold: float = 0.5
     cost_change_threshold: float = 0.3


