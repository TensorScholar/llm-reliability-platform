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


 class HallucinationDetectionInvariant(AbstractInvariant):
     """Detects potential hallucination indicators (hedging, contradictions, temporal issues)."""

     HEDGE_WORDS = [
         "might",
         "may",
         "could",
         "possibly",
         "perhaps",
         "likely",
         "probably",
         "seems",
         "appears",
         "suggests",
         "indicates",
     ]

     ABSOLUTE_PHRASES = [
         "definitely",
         "certainly",
         "absolutely",
         "without doubt",
         "guaranteed",
         "always",
         "never",
         "impossible",
     ]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="factuality.hallucination_detection",
             name="Hallucination Detection",
             description="Detects potential hallucinations and fabricated information",
             category=InvariantCategory.FACTUALITY,
             version="1.0.0",
             tags={"factuality", "hallucination", "accuracy"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start_time = asyncio.get_event_loop().time()
         text = context.response.text
         evidence: list[ValidationEvidence] = []

         # Excessive hedging
         hedge_count = self._count_hedge_words(text)
         word_count = len(text.split()) or 1
         hedge_ratio = hedge_count / word_count
         if hedge_ratio > 0.05:
             evidence.append(
                 ValidationEvidence(
                     description="Excessive hedging detected",
                     extracted_text=f"{hedge_count} hedge words in {word_count} words ({hedge_ratio:.1%})",
                     confidence_score=0.6,
                     metadata={"hedge_count": hedge_count, "hedge_ratio": hedge_ratio},
                 )
             )

         # Contradictions
         contradictions = self._detect_contradictions(text)
         if contradictions:
             evidence.append(
                 ValidationEvidence(
                     description="Contradictory absolute statements detected",
                     extracted_text="; ".join(contradictions[:3]),
                     confidence_score=0.75,
                     metadata={"contradiction_count": len(contradictions)},
                 )
             )

         # Temporal inconsistencies
         temporal_issue = self._detect_temporal_issues(text)
         if temporal_issue:
             evidence.append(
                 ValidationEvidence(
                     description="Temporal inconsistencies detected",
                     extracted_text=temporal_issue,
                     confidence_score=0.8,
                     metadata={"issue_type": "temporal"},
                 )
             )

         exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

         if evidence:
             avg_conf = sum(e.confidence_score or 0 for e in evidence) / len(evidence)
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message=f"Detected {len(evidence)} hallucination indicator(s) (confidence: {avg_conf:.0%})",
                 evidence=evidence,
                 execution_time_ms=exec_ms,
             )

         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="No hallucination indicators detected",
             execution_time_ms=exec_ms,
         )

     def _count_hedge_words(self, text: str) -> int:
         tl = text.lower()
         return sum(len(re.findall(r"\b" + re.escape(w) + r"\b", tl)) for w in self.HEDGE_WORDS)

     def _detect_contradictions(self, text: str) -> List[str]:
         contradictions: list[str] = []
         tl = text.lower()
         if "always" in tl and "never" in tl:
             contradictions.append("Contains both 'always' and 'never' statements")
         if "impossible" in tl and "definitely" in tl:
             contradictions.append("Contains both 'impossible' and 'definitely' statements")

         sentences = text.split(".")
         for i, sent in enumerate(sentences):
             if " not " in sent.lower():
                 opposite = sent.lower().replace(" not ", " ")
                 for j, other in enumerate(sentences):
                     if i != j and opposite.strip() and opposite in other.lower():
                         contradictions.append("Possible contradiction between statements")
                         break
         return contradictions

     def _detect_temporal_issues(self, text: str) -> str | None:
         from datetime import datetime

         current_year = datetime.now().year
         pattern = r"\b(in|during|by)\s+(\d{4})\b"
         for prep, year_str in re.findall(pattern, text.lower()):
             year = int(year_str)
             if year > current_year and prep in ["in", "during"]:
                 return f"References future year {year} as past event"
         return None


