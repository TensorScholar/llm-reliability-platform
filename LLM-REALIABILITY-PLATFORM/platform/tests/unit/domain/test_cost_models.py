from __future__ import annotations

from datetime import datetime, timedelta

from reliability_platform.domain.models.cost import (
    CostAggregation,
    CostBreakdown,
    CostCategory,
    CostImpact,
    ImpactLevel,
)


def test_cost_models():
    cb = CostBreakdown(infrastructure_usd=1.0, operational_usd=2.0)
    assert cb.total_usd == 3.0

    ci = CostImpact(
        impact_level=ImpactLevel.MEDIUM,
        cost_breakdown=cb,
        description="Latency spike",
        calculation_method="rule",
        confidence_score=0.8,
    )
    assert ci.total_cost_usd == 3.0

    agg = CostAggregation(
        period_start=datetime.utcnow() - timedelta(hours=1),
        period_end=datetime.utcnow(),
        total_events=10,
        total_failures=2,
        total_cost_usd=20.0,
        cost_by_category={CostCategory.INFRASTRUCTURE: 10.0},
        cost_by_severity={"high": 12.0},
        top_cost_drivers=[{"name": "tokens"}],
    )
    assert agg.average_cost_per_event == 2.0
    assert agg.average_cost_per_failure == 10.0
