 from __future__ import annotations

 from dataclasses import dataclass, field
 from datetime import datetime
 from enum import Enum
 from typing import Any, Dict, List, Optional
 from uuid import UUID, uuid4


 class ModelProvider(str, Enum):
     """Supported LLM providers."""

     OPENAI = "openai"
     ANTHROPIC = "anthropic"
     COHERE = "cohere"
     HUGGINGFACE = "huggingface"
     CUSTOM = "custom"


 class RequestType(str, Enum):
     """Type of LLM request."""

     CHAT = "chat"
     COMPLETION = "completion"
     EMBEDDING = "embedding"
     CLASSIFICATION = "classification"


 @dataclass(frozen=True)
 class ModelConfig:
     """Immutable model configuration."""

     provider: ModelProvider = ModelProvider.OPENAI
     model_name: str = "gpt-4o"
     model_version: Optional[str] = None
     temperature: float = 0.7
     max_tokens: Optional[int] = None
     top_p: float = 1.0
     frequency_penalty: float = 0.0
     presence_penalty: float = 0.0

     def __post_init__(self) -> None:
         if not 0 <= self.temperature <= 2:
             raise ValueError("Temperature must be between 0 and 2")
         if not 0 <= self.top_p <= 1:
             raise ValueError("top_p must be between 0 and 1")


 @dataclass(frozen=True)
 class RequestContext:
     """Context information for the request."""

     user_id: Optional[str] = None
     session_id: Optional[str] = None
     request_id: Optional[str] = None
     ab_variant: Optional[str] = None
     environment: str = "production"
     application_name: str = "default"
     custom_metadata: Dict[str, Any] = field(default_factory=dict)


 @dataclass(frozen=True)
 class LLMRequest:
     """Immutable LLM request representation."""

     id: UUID = field(default_factory=uuid4)
     request_type: RequestType = RequestType.CHAT
     prompt: str = ""
     messages: List[Dict[str, str]] = field(default_factory=list)
     model_config: ModelConfig = field(default_factory=lambda: ModelConfig())
     context: RequestContext = field(default_factory=RequestContext)
     timestamp: datetime = field(default_factory=datetime.utcnow)

     def __post_init__(self) -> None:
         if not self.prompt and not self.messages:
             raise ValueError("Either prompt or messages must be provided")

     @property
     def estimated_tokens(self) -> int:
         """Rough token count estimation (4 chars = 1 token)."""

         text = self.prompt or " ".join(m.get("content", "") for m in self.messages)
         return len(text) // 4


 @dataclass(frozen=True)
 class LLMResponse:
     """Immutable LLM response representation."""

     id: UUID = field(default_factory=uuid4)
     request_id: UUID = field(default_factory=uuid4)
     text: str = ""
     finish_reason: Optional[str] = None
     model_used: Optional[str] = None
     usage: Dict[str, int] = field(default_factory=dict)  # tokens_prompt, tokens_completion
     latency_ms: int = 0
     timestamp: datetime = field(default_factory=datetime.utcnow)

     @property
     def total_tokens(self) -> int:
         """Total tokens used."""

         return self.usage.get("tokens_prompt", 0) + self.usage.get("tokens_completion", 0)

     @property
     def cost_usd(self) -> float:
         """Estimated cost in USD (simplified)."""

         # Simplified: $0.002 per 1K tokens (placeholder pricing)
         return (self.total_tokens / 1000) * 0.002


 @dataclass(frozen=True)
 class CaptureEvent:
     """Complete capture event combining request and response."""

     id: UUID = field(default_factory=uuid4)
     request: LLMRequest = field(default_factory=LLMRequest)
     response: LLMResponse = field(default_factory=LLMResponse)
     captured_at: datetime = field(default_factory=datetime.utcnow)
     sdk_version: str = "1.0.0"

     def to_dict(self) -> Dict[str, Any]:
         """Serialize to dictionary for storage/transmission."""

         return {
             "id": str(self.id),
             "request": {
                 "id": str(self.request.id),
                 "request_type": self.request.request_type.value,
                 "prompt": self.request.prompt,
                 "messages": self.request.messages,
                 "model_config": {
                     "provider": self.request.model_config.provider.value,
                     "model_name": self.request.model_config.model_name,
                     "temperature": self.request.model_config.temperature,
                 },
                 "context": {
                     "user_id": self.request.context.user_id,
                     "session_id": self.request.context.session_id,
                     "application_name": self.request.context.application_name,
                     "custom_metadata": self.request.context.custom_metadata,
                 },
                 "timestamp": self.request.timestamp.isoformat(),
             },
             "response": {
                 "id": str(self.response.id),
                 "request_id": str(self.response.request_id),
                 "text": self.response.text,
                 "usage": self.response.usage,
                 "latency_ms": self.response.latency_ms,
                 "timestamp": self.response.timestamp.isoformat(),
             },
             "captured_at": self.captured_at.isoformat(),
             "sdk_version": self.sdk_version,
         }


