from __future__ import annotations

from datetime import datetime, timedelta

from reliability_platform.domain.models.drift import (
    DistributionMetrics,
    DriftAlert,
    DriftMetric,
    DriftSeverity,
    DriftType,
    DriftWindow,
)


def test_drift_models():
    now = datetime.utcnow()
    base = DriftWindow(start=now - timedelta(hours=2), end=now - timedelta(hours=1), label="base")
    comp = DriftWindow(start=now - timedelta(minutes=30), end=now, label="curr")

    metrics = DistributionMetrics.from_samples([1.0, 2.0, 3.0])
    assert metrics.sample_count == 3
    assert metrics.max_value == 3.0

    dm = DriftMetric(
        drift_type=DriftType.STATISTICAL,
        metric_name="kl_divergence",
        value=0.2,
        threshold=0.1,
        severity=DriftSeverity.HIGH,
        baseline_window=base,
        comparison_window=comp,
        metadata={"application_name": "app"},
    )
    assert dm.is_drifting
    assert dm.drift_ratio > 1.0

    alert = DriftAlert(
        drift_metrics=[dm],
        overall_severity=DriftSeverity.HIGH,
        title="Drift detected",
    )
    assert alert.is_critical
    assert alert.drift_count == 1

    d = dm.to_dict()
    assert d["metric_name"] == "kl_divergence"
