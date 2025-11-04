from __future__ import annotations

from reliability_platform.domain.models.validation import (
    Severity,
    ValidationEvidence,
    ValidationResult,
    ValidationStatus,
)


def test_validation_result_properties_and_dict():
    ev = ValidationEvidence(description="matched", extracted_text="abc", confidence_score=0.9)
    vr = ValidationResult(
        invariant_id="inv-1",
        status=ValidationStatus.FAILED,
        severity=Severity.HIGH,
        message="Violation found",
        evidence=[ev],
        execution_time_ms=12,
    )
    assert not vr.passed
    assert vr.requires_action

    d = vr.to_dict()
    assert d["status"] == "failed"
    assert d["severity"] == "high"
    assert d["evidence"][0]["description"] == "matched"
