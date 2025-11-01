from __future__ import annotations

import asyncio
import os
import structlog

from reliability_platform.infrastructure.messaging.kafka_consumer import KafkaConsumerClient
from reliability_platform.infrastructure.messaging.topics import KafkaTopics


logger = structlog.get_logger()


async def handle_capture(message: dict) -> None:
	# Placeholder: perform validation here
	logger.info("validation_worker_received", capture_id=message.get("id"))


async def main() -> None:
	bootstrap = os.getenv("KAFKA__BOOTSTRAP_SERVERS", "localhost:9092")
	consumer = KafkaConsumerClient(
		bootstrap_servers=bootstrap,
		group_id="validation-workers",
		topics=[KafkaTopics.CAPTURES_RAW],
		handler=handle_capture,
	)
	await consumer.start()
	try:
		await consumer.consume()
	finally:
		await consumer.stop()


if __name__ == "__main__":
	asyncio.run(main())
