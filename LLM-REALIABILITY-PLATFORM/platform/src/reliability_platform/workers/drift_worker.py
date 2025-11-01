from __future__ import annotations

import asyncio
import os
from datetime import timedelta
import structlog


logger = structlog.get_logger()


async def run_once() -> None:
	# Placeholder: fetch data and run drift detection here
	logger.info("drift_worker_run")


async def main() -> None:
	interval_minutes = int(os.getenv("DRIFT__INTERVAL_MINUTES", "15"))
	while True:
		await run_once()
		await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
	asyncio.run(main())
