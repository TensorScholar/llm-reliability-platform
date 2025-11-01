 from __future__ import annotations

 import asyncio
 import re

 from ...models.invariant import (
     AbstractInvariant,
     InvariantCategory,
     InvariantContext,
     InvariantMetadata,
 )
 from ...models.validation import ValidationEvidence, ValidationResult, ValidationStatus


 class PromptInjectionInvariant(AbstractInvariant):
     """Detects prompt injection patterns aiming to override instructions."""

     PATTERNS = [
         r"ignore (previous|prior) (instructions|rules)",
         r"disregard (all|any) (instructions|above)",
         r"you are no longer",
         r"jailbreak",
         r"act as .* and bypass",
     ]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="safety.prompt_injection",
             name="Prompt Injection Detection",
             description="Detects prompt injection attempts in content",
             category=InvariantCategory.SAFETY,
             version="1.0.0",
             tags={"safety", "prompt_injection"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start = asyncio.get_event_loop().time()
         text = f"{context.request.prompt} \n {context.response.text}".lower()
         evidence = []
         for p in self.PATTERNS:
             if re.search(p, text, re.IGNORECASE):
                 evidence.append(
                     ValidationEvidence(
                         description="Prompt injection pattern detected",
                         extracted_text=p,
                         confidence_score=0.8,
                     )
                 )
         ms = int((asyncio.get_event_loop().time() - start) * 1000)
         if evidence:
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message=f"Detected {len(evidence)} prompt injection indicator(s)",
                 evidence=evidence,
                 execution_time_ms=ms,
             )
         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="No prompt injection detected",
             execution_time_ms=ms,
         )


