from __future__ import annotations

from datetime import datetime
from uuid import UUID

from reliability_platform.domain.models.capture import (
    CaptureEvent,
    LLMRequest,
    LLMResponse,
    ModelConfig,
    ModelProvider,
    RequestContext,
    RequestType,
)


def test_capture_event_roundtrip():
    cfg = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", temperature=0.2)
    ctx = RequestContext(user_id="u1", session_id="s1", application_name="app")
    req = LLMRequest(
        request_type=RequestType.CHAT,
        prompt="Hello world",
        model_config=cfg,
        context=ctx,
    )
    resp = LLMResponse(
        request_id=req.id,
        text="Hi!",
        usage={"tokens_prompt": 5, "tokens_completion": 7},
        latency_ms=42,
    )
    cap = CaptureEvent(request=req, response=resp, sdk_version="0.1.0")

    d = cap.to_dict()
    assert d["id"]
    assert d["request"]["request_type"] == "chat"
    assert d["response"]["latency_ms"] == 42

    # properties
    assert req.estimated_tokens >= 2
    assert resp.total_tokens == 12
    assert resp.cost_usd >= 0.0
