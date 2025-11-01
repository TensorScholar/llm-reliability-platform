 from __future__ import annotations

 import asyncio
 from typing import List, Optional

 import structlog

 from ....domain.models.capture import CaptureEvent
 from ....domain.models.invariant import AbstractInvariant, InvariantContext, InvariantRegistry
 from ....domain.models.validation import (
     ValidationResult,
     ValidationStatus,
 )


 logger = structlog.get_logger()


 class ValidationService:
     """Service for validating capture events against invariant rules."""

     def __init__(
         self,
         invariant_registry: InvariantRegistry,
         max_parallel: int = 10,
         default_timeout_ms: int = 5000,
     ) -> None:
         self.invariant_registry = invariant_registry
         self.max_parallel = max_parallel
         self.default_timeout_ms = default_timeout_ms
         self.semaphore = asyncio.Semaphore(max_parallel)

     async def validate_capture(
         self, capture_event: CaptureEvent, invariant_ids: Optional[List[str]] = None
     ) -> List[ValidationResult]:
         logger.info(
             "validating_capture",
             capture_id=str(capture_event.id),
             invariant_ids=invariant_ids,
         )

         invariants: List[AbstractInvariant]
         if invariant_ids:
             invariants = [
                 self.invariant_registry.get(inv_id)
                 for inv_id in invariant_ids
                 if self.invariant_registry.get(inv_id)
             ]  # type: ignore[list-item]
             invariants = [i for i in invariants if i is not None]
         else:
             invariants = self.invariant_registry.get_enabled()

         context = InvariantContext(capture_event=capture_event)
         applicable = [inv for inv in invariants if inv.should_apply(context)]
         logger.info(
             "executing_invariants",
             total_invariants=len(invariants),
             applicable_invariants=len(applicable),
         )

         results = await self._execute_invariants_parallel(applicable, context)
         passed = sum(1 for r in results if r.passed)
         failed = sum(1 for r in results if not r.passed)
         logger.info(
             "validation_complete",
             capture_id=str(capture_event.id),
             total=len(results),
             passed=passed,
             failed=failed,
         )
         return results

     async def _execute_invariants_parallel(
         self, invariants: List[AbstractInvariant], context: InvariantContext
     ) -> List[ValidationResult]:
         tasks = [self._execute_single_invariant(inv, context) for inv in invariants]
         results = await asyncio.gather(*tasks, return_exceptions=True)

         processed: List[ValidationResult] = []
         for inv, result in zip(invariants, results):
             if isinstance(result, Exception):
                 logger.error(
                     "invariant_execution_error",
                     invariant_id=inv.metadata.id,
                     error=str(result),
                 )
                 processed.append(
                     ValidationResult(
                         invariant_id=inv.metadata.id,
                         capture_event_id=context.capture_event.id,
                         status=ValidationStatus.ERROR,
                         severity=inv.config.severity,
                         message=f"Execution error: {str(result)}",
                     )
                 )
             else:
                 processed.append(result)
         return processed

     async def _execute_single_invariant(
         self, invariant: AbstractInvariant, context: InvariantContext
     ) -> ValidationResult:
         async with self.semaphore:
             timeout_ms = invariant.config.timeout_ms or self.default_timeout_ms
             max_retries = invariant.config.max_retries if invariant.config.retry_on_error else 0
             for attempt in range(max_retries + 1):
                 try:
                     return await asyncio.wait_for(
                         invariant.validate(context), timeout=timeout_ms / 1000.0
                     )
                 except asyncio.TimeoutError:
                     logger.warning(
                         "invariant_timeout",
                         invariant_id=invariant.metadata.id,
                         timeout_ms=timeout_ms,
                         attempt=attempt + 1,
                     )
                     if attempt >= max_retries:
                         return ValidationResult(
                             invariant_id=invariant.metadata.id,
                             capture_event_id=context.capture_event.id,
                             status=ValidationStatus.ERROR,
                             severity=invariant.config.severity,
                             message=f"Execution timeout after {timeout_ms}ms",
                         )
                 except Exception as e:  # noqa: BLE001
                     logger.error(
                         "invariant_error",
                         invariant_id=invariant.metadata.id,
                         error=str(e),
                         attempt=attempt + 1,
                     )
                     if attempt >= max_retries:
                         raise
                 await asyncio.sleep(0.1 * (2**attempt))


