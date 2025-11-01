 from __future__ import annotations

 import asyncio
 import re
 from typing import List

 from ...models.invariant import (
     AbstractInvariant,
     InvariantMetadata,
     InvariantCategory,
     InvariantContext,
 )
 from ...models.validation import ValidationResult, ValidationStatus, ValidationEvidence


 class SourceAttributionInvariant(AbstractInvariant):
     """Ensures factual claims are attributed to sources."""

     CLAIM_INDICATORS = [
         r"according to",
         r"studies show",
         r"research indicates",
         r"data shows",
         r"statistics reveal",
         r"experts say",
         r"\d+% of",
         r"in \d{4}",
     ]

     SOURCE_PATTERNS = [
         r"\(.*?\d{4}.*?\)",
         r"\[.*?\]",
         r"https?://",
         r"according to .+? \(",
         r"as reported by",
         r"source:",
     ]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="factuality.source_attribution",
             name="Source Attribution",
             description="Ensures factual claims are attributed to verifiable sources",
             category=InvariantCategory.FACTUALITY,
             version="1.0.0",
             tags={"factuality", "sources", "attribution", "citations"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start_time = asyncio.get_event_loop().time()

         text = context.response.text
         claims = self._extract_claim_sentences(text)

         if not claims:
             exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
             return self._create_result(
                 context=context,
                 status=ValidationStatus.PASSED,
                 message="No factual claims requiring attribution detected",
                 execution_time_ms=exec_ms,
             )

         unsourced = [s for s in claims if not self._has_source_attribution(s)]

         exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
         domain = self._detect_domain(text)
         strict = domain in ["financial", "medical", "legal"]

         if unsourced:
             evidence = [
                 ValidationEvidence(
                     description=f"Unsourced claim in {domain} domain",
                     extracted_text=claim[:200],
                     confidence_score=0.8,
                     metadata={"domain": domain, "requires_strict": strict},
                 )
                 for claim in unsourced[:5]
             ]

             status = (
                 ValidationStatus.FAILED
                 if strict or len(unsourced) > 3
                 else ValidationStatus.PASSED
             )
             message = (
                 f"{len(unsourced)} unsourced claims in {domain} domain"
                 if strict
                 else f"{len(unsourced)} claims without explicit source attribution"
             )
             return self._create_result(
                 context=context,
                 status=status,
                 message=message,
                 evidence=evidence,
                 execution_time_ms=exec_ms,
             )

         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message=f"All {len(claims)} factual claims properly attributed",
             execution_time_ms=exec_ms,
         )

     def _extract_claim_sentences(self, text: str) -> List[str]:
         sentences = re.split(r"[.!?]+", text)
         out: list[str] = []
         for s in sentences:
             candidate = s.strip()
             if not candidate:
                 continue
             if any(re.search(p, candidate, re.IGNORECASE) for p in self.CLAIM_INDICATORS):
                 out.append(candidate)
         return out

     def _has_source_attribution(self, sentence: str) -> bool:
         return any(re.search(p, sentence, re.IGNORECASE) for p in self.SOURCE_PATTERNS)

     def _detect_domain(self, text: str) -> str:
         t = text.lower()
         financial = ["stock", "investment", "portfolio", "trading", "financial", "market"]
         medical = ["medical", "diagnosis", "treatment", "symptom", "disease", "patient"]
         legal = ["legal", "law", "court", "attorney", "contract", "lawsuit"]
         if any(k in t for k in financial):
             return "financial"
         if any(k in t for k in medical):
             return "medical"
         if any(k in t for k in legal):
             return "legal"
         return "general"


