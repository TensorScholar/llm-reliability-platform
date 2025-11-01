 from __future__ import annotations

 import asyncio
 import re

 from ...models.invariant import (
     AbstractInvariant,
     InvariantMetadata,
     InvariantCategory,
     InvariantContext,
 )
 from ...models.validation import ValidationResult, ValidationStatus, ValidationEvidence


 class MedicalDisclaimerInvariant(AbstractInvariant):
     """Ensures medical/health responses include appropriate disclaimers."""

     MEDICAL_KEYWORDS = [
         "symptom",
         "diagnosis",
         "treatment",
         "medication",
         "disease",
         "condition",
         "doctor",
         "physician",
         "medical",
         "health",
         "prescription",
         "therapy",
         "cure",
         "illness",
     ]

     DISCLAIMER_PATTERNS = [
         r"consult.*?(doctor|physician|healthcare professional)",
         r"seek.*?medical advice",
         r"not.*?substitute.*?professional",
         r"this is not medical advice",
         r"speak.*?healthcare provider",
     ]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="compliance.medical_disclaimer",
             name="Medical Disclaimer",
             description="Ensures medical content includes appropriate disclaimers",
             category=InvariantCategory.COMPLIANCE,
             version="1.0.0",
             tags={"compliance", "medical", "legal", "disclaimer"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start_time = asyncio.get_event_loop().time()

         text = context.response.text
         t = text.lower()

         medical_keyword_count = sum(1 for kw in self.MEDICAL_KEYWORDS if kw in t)
         if medical_keyword_count == 0:
             exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
             return self._create_result(
                 context=context,
                 status=ValidationStatus.PASSED,
                 message="Not medical content - disclaimer not required",
                 execution_time_ms=exec_ms,
             )

         has_disclaimer = any(re.search(pat, t) for pat in self.DISCLAIMER_PATTERNS)
         exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

         if not has_disclaimer:
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message=(
                     f"Medical content detected ({medical_keyword_count} keywords) but no disclaimer found"
                 ),
                 evidence=[
                     ValidationEvidence(
                         description="Missing required medical disclaimer",
                         extracted_text="Content discusses medical topics but lacks disclaimer",
                         confidence_score=0.9,
                         metadata={"medical_keyword_count": medical_keyword_count},
                     )
                 ],
                 execution_time_ms=exec_ms,
             )

         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="Medical content includes appropriate disclaimer",
             execution_time_ms=exec_ms,
         )


