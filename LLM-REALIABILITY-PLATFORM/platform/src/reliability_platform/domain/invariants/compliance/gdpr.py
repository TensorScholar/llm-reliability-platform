 from __future__ import annotations

 import asyncio

 from ...models.invariant import (
     AbstractInvariant,
     InvariantCategory,
     InvariantContext,
     InvariantMetadata,
 )
 from ...models.validation import ValidationEvidence, ValidationResult, ValidationStatus


 class GDPRComplianceInvariant(AbstractInvariant):
     """Checks for GDPR-related disclaimers when handling personal data mentions."""

     KEYWORDS = ["personal data", "gdpr", "data protection", "eu regulation 2016/679"]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="compliance.gdpr",
             name="GDPR Compliance",
             description="Ensures GDPR disclaimer when personal data is discussed",
             category=InvariantCategory.COMPLIANCE,
             version="1.0.0",
             tags={"compliance", "gdpr"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start = asyncio.get_event_loop().time()
         text = context.response.text.lower()
         mentions_pd = any(k in text for k in self.KEYWORDS)
         has_disclaimer = "gdpr" in text or "data protection" in text
         ms = int((asyncio.get_event_loop().time() - start) * 1000)
         if mentions_pd and not has_disclaimer:
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message="Mentions personal data without GDPR disclaimer",
                 evidence=[
                     ValidationEvidence(
                         description="Missing GDPR disclaimer",
                         extracted_text=text[:200],
                         confidence_score=0.7,
                     )
                 ],
                 execution_time_ms=ms,
             )
         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="GDPR compliance ok or not applicable",
             execution_time_ms=ms,
         )


