 from __future__ import annotations

 from datetime import datetime
 from typing import Any, Dict, List, Optional
 from uuid import UUID, uuid4

 from pydantic import BaseModel, Field


 class CaptureEventDTO(BaseModel):
     id: UUID = Field(default_factory=uuid4)
     request_id: str
     request_type: str
     prompt: Optional[str] = None
     messages: Optional[List[Dict[str, str]]] = None
     model_provider: str
     model_name: str
     temperature: float = 0.7
     response_text: str
     finish_reason: Optional[str] = None
     tokens_prompt: Optional[int] = None
     tokens_completion: Optional[int] = None
     latency_ms: int
     user_id: Optional[str] = None
     session_id: Optional[str] = None
     application_name: str = "default"
     ab_variant: Optional[str] = None
     custom_metadata: Dict[str, Any] = Field(default_factory=dict)
     timestamp: datetime = Field(default_factory=datetime.utcnow)

     @classmethod
     def from_request(cls, request_model: Any) -> "CaptureEventDTO":
         data = request_model.model_dump() if hasattr(request_model, "model_dump") else dict(request_model)
         if not data.get("timestamp"):
             data["timestamp"] = datetime.utcnow()
         return cls(**data)

     def to_dict(self) -> Dict[str, Any]:
         d = self.model_dump()
         d["id"] = str(self.id)
         d["timestamp"] = self.timestamp.isoformat()
         return d


