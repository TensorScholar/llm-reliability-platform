 from __future__ import annotations

 import asyncio
 import json
 from typing import Any, Dict, Optional

 import structlog
 from aiokafka import AIOKafkaProducer
 from aiokafka.errors import KafkaError

 from .topics import KafkaTopics


 logger = structlog.get_logger()


 class KafkaProducerClient:
     """Async Kafka producer with error handling and retries."""

     def __init__(
         self,
         bootstrap_servers: str,
         client_id: str = "reliability-platform",
         compression_type: str = "gzip",
     ) -> None:
         self.bootstrap_servers = bootstrap_servers
         self.client_id = client_id
         self.compression_type = compression_type
         self.producer: Optional[AIOKafkaProducer] = None
         self._lock = asyncio.Lock()

     async def start(self) -> None:
         async with self._lock:
             if self.producer is None:
                 self.producer = AIOKafkaProducer(
                     bootstrap_servers=self.bootstrap_servers,
                     client_id=self.client_id,
                     compression_type=self.compression_type,
                     value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                     key_serializer=lambda k: k.encode("utf-8") if k else None,
                     acks="all",
                     retries=3,
                     max_in_flight_requests_per_connection=5,
                 )
                 await self.producer.start()
                 logger.info("kafka_producer_started")

     async def stop(self) -> None:
         async with self._lock:
             if self.producer:
                 await self.producer.stop()
                 self.producer = None
                 logger.info("kafka_producer_stopped")

     async def send(
         self,
         topic: KafkaTopics,
         value: Dict[str, Any],
         key: Optional[str] = None,
         headers: Optional[Dict[str, str]] = None,
     ) -> bool:
         if not self.producer:
             logger.error("kafka_producer_not_started")
             return False

         try:
             kafka_headers = None
             if headers:
                 kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

             future = await self.producer.send(
                 topic.value,
                 value=value,
                 key=key,
                 headers=kafka_headers,
             )
             record_metadata = await future
             logger.debug(
                 "kafka_message_sent",
                 topic=topic.value,
                 partition=record_metadata.partition,
                 offset=record_metadata.offset,
             )
             return True
         except KafkaError as e:
             logger.error("kafka_send_error", topic=topic.value, error=str(e))
             return False
         except Exception as e:  # noqa: BLE001
             logger.error("kafka_send_unexpected_error", topic=topic.value, error=str(e))
             return False


