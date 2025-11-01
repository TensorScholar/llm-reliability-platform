 from __future__ import annotations

 import asyncio

 from ...models.invariant import (
     AbstractInvariant,
     InvariantCategory,
     InvariantContext,
     InvariantMetadata,
 )
 from ...models.validation import ValidationEvidence, ValidationResult, ValidationStatus


 class ConsistencyInvariant(AbstractInvariant):
     """Checks basic internal consistency like repeated facts in response body."""

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="factuality.consistency",
             name="Consistency Check",
             description="Detects simple internal inconsistencies in the response",
             category=InvariantCategory.FACTUALITY,
             version="1.0.0",
             tags={"factuality", "consistency"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start = asyncio.get_event_loop().time()
         text = context.response.text
         evidence = []
         # Simple heuristic: if the same numeric value appears with two different units line-by-line
         lines = [l.strip() for l in text.splitlines() if l.strip()]
         seen_numbers: dict[str, str] = {}
         for line in lines:
             for token in line.split():
                 if token.isdigit():
                     unit = "words" if "word" in line.lower() else "units"
                     prev = seen_numbers.get(token)
                     if prev and prev != unit:
                         evidence.append(
                             ValidationEvidence(
                                 description="Potential inconsistency for numeric value",
                                 extracted_text=line[:200],
                                 confidence_score=0.5,
                             )
                         )
                     else:
                         seen_numbers[token] = unit
         ms = int((asyncio.get_event_loop().time() - start) * 1000)
         if evidence:
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message=f"Detected {len(evidence)} potential inconsistency(ies)",
                 evidence=evidence,
                 execution_time_ms=ms,
             )
         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="No obvious inconsistencies detected",
             execution_time_ms=ms,
         )


