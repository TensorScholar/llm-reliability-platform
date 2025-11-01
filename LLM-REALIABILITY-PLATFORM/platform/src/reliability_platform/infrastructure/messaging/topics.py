 from enum import Enum


 class KafkaTopics(str, Enum):
     """Kafka topic names."""

     CAPTURES_RAW = "llm.captures.raw"
     CAPTURES_ENRICHED = "llm.captures.enriched"
     VALIDATIONS_RESULTS = "llm.validations.results"
     DRIFT_ALERTS = "llm.drift.alerts"
     ALERTS_CRITICAL = "llm.alerts.critical"
     COST_IMPACTS = "llm.cost.impacts"


