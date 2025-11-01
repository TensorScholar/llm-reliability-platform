 from __future__ import annotations

 from pydantic import BaseModel, Field, HttpUrl


 class SDKConfig(BaseModel):
     api_url: HttpUrl
     api_key: str | None = None
     application_name: str = "default"
     timeout_seconds: float = 5.0
     buffer_max_size: int = 1000
     buffer_flush_interval: float = 2.0
     sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)
     sampling_strategy: str = "uniform"


