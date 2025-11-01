 from __future__ import annotations

 from typing import List, Optional

 from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, field_validator
 from pydantic_settings import BaseSettings, SettingsConfigDict


 class DatabaseSettings(BaseModel):
     url: PostgresDsn
     pool_size: int = 20
     max_overflow: int = 10
     echo: bool = False


 class KafkaSettings(BaseModel):
     bootstrap_servers: str = "localhost:9092"
     client_id: str = "reliability-platform"
     compression_type: str = "gzip"


 class RedisSettings(BaseModel):
     url: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore[assignment]
     max_connections: int = 50


 class APISettings(BaseModel):
     host: str = "0.0.0.0"
     port: int = 8000
     cors_origins: List[str] = ["*"]
     rate_limit_per_minute: int = 1000


 class InvariantSettings(BaseModel):
     enabled: bool = True
     max_parallel: int = 10
     default_timeout_ms: int = 5000


 class DriftDetectionSettings(BaseModel):
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


 class ObservabilitySettings(BaseModel):
     log_level: str = "INFO"
     structured_logging: bool = True
     enable_tracing: bool = False
     tracing_endpoint: Optional[str] = None
     metrics_port: int = 9090


 class Settings(BaseSettings):
     model_config = SettingsConfigDict(
         env_file=".env",
         env_nested_delimiter="__",
         case_sensitive=False,
     )

     environment: str = "development"
     debug: bool = False

     database: DatabaseSettings
     kafka: KafkaSettings = KafkaSettings()
     redis: RedisSettings = RedisSettings()
     api: APISettings = APISettings()
     invariants: InvariantSettings = InvariantSettings()
     drift_detection: DriftDetectionSettings = DriftDetectionSettings()
     observability: ObservabilitySettings = ObservabilitySettings()

     @field_validator("environment")
     @classmethod
     def validate_environment(cls, v: str) -> str:
         allowed = ["development", "staging", "production"]
         if v not in allowed:
             raise ValueError(f"Environment must be one of {allowed}")
         return v


 def get_settings() -> Settings:
     return Settings()


