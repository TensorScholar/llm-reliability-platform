 from __future__ import annotations

 import asyncio
 import json
 from typing import Awaitable, Callable, Optional

 import structlog
 from aiokafka import AIOKafkaConsumer
 from aiokafka.errors import KafkaError

 from .topics import KafkaTopics


 logger = structlog.get_logger()

 MessageHandler = Callable[[dict], Awaitable[None]]


 class KafkaConsumerClient:
     def __init__(
         self,
         bootstrap_servers: str,
         group_id: str,
         topics: list[KafkaTopics],
         handler: MessageHandler,
         auto_offset_reset: str = "earliest",
         enable_auto_commit: bool = True,
     ) -> None:
         self.bootstrap_servers = bootstrap_servers
         self.group_id = group_id
         self.topics = [t.value for t in topics]
         self.handler = handler
         self.auto_offset_reset = auto_offset_reset
         self.enable_auto_commit = enable_auto_commit
         self.consumer: Optional[AIOKafkaConsumer] = None
         self._running = False

     async def start(self) -> None:
         self.consumer = AIOKafkaConsumer(
             *self.topics,
             bootstrap_servers=self.bootstrap_servers,
             group_id=self.group_id,
             auto_offset_reset=self.auto_offset_reset,
             enable_auto_commit=self.enable_auto_commit,
             value_deserializer=lambda m: json.loads(m.decode("utf-8")),
             key_deserializer=lambda k: k.decode("utf-8") if k else None,
         )
         await self.consumer.start()
         self._running = True
         logger.info("kafka_consumer_started", group_id=self.group_id, topics=self.topics)

     async def stop(self) -> None:
         self._running = False
         if self.consumer:
             await self.consumer.stop()
             logger.info("kafka_consumer_stopped")

     async def consume(self) -> None:
         if not self.consumer:
             raise RuntimeError("Consumer not started")
         try:
             async for message in self.consumer:
                 if not self._running:
                     break
                 try:
                     logger.debug(
                         "kafka_message_received",
                         topic=message.topic,
                         partition=message.partition,
                         offset=message.offset,
                     )
                     await self.handler(message.value)
                 except Exception as e:  # noqa: BLE001
                     logger.error(
                         "kafka_handler_error",
                         topic=message.topic,
                         error=str(e),
                         offset=message.offset,
                     )
         except KafkaError as e:
             logger.error("kafka_consume_error", error=str(e))
             raise


