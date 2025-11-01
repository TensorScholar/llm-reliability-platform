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


 class FinancialWarningsInvariant(AbstractInvariant):
     """Ensures financial content includes appropriate warnings."""

     FINANCIAL_KEYWORDS = [
         "invest",
         "stock",
         "trading",
         "portfolio",
         "return",
         "profit",
         "dividend",
         "cryptocurrency",
         "crypto",
         "bitcoin",
         "market",
         "financial advice",
         "buy",
         "sell",
     ]

     WARNING_PATTERNS = [
         r"not financial advice",
         r"consult.*?financial advisor",
         r"past performance.*?not.*?guarantee",
         r"risk.*?loss",
         r"do your own research",
         r"DYOR",
     ]

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="compliance.financial_warnings",
             name="Financial Warnings",
             description="Ensures financial content includes appropriate warnings",
             category=InvariantCategory.COMPLIANCE,
             version="1.0.0",
             tags={"compliance", "financial", "legal", "warnings"},
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start_time = asyncio.get_event_loop().time()

         text = context.response.text
         t = text.lower()

         fin_keyword_count = sum(1 for kw in self.FINANCIAL_KEYWORDS if kw in t)
         if fin_keyword_count == 0:
             exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
             return self._create_result(
                 context=context,
                 status=ValidationStatus.PASSED,
                 message="Not financial content - warning not required",
                 execution_time_ms=exec_ms,
             )

         has_warning = any(re.search(p, t) for p in self.WARNING_PATTERNS)
         exec_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

         if not has_warning:
             return self._create_result(
                 context=context,
                 status=ValidationStatus.FAILED,
                 message=(
                     f"Financial content detected ({fin_keyword_count} keywords) but no warning found"
                 ),
                 evidence=[
                     ValidationEvidence(
                         description="Missing required financial warning",
                         extracted_text=(
                             "Content provides financial information without appropriate disclaimers"
                         ),
                         confidence_score=0.95,
                         metadata={"financial_keyword_count": fin_keyword_count},
                     )
                 ],
                 execution_time_ms=exec_ms,
             )

         return self._create_result(
             context=context,
             status=ValidationStatus.PASSED,
             message="Financial content includes appropriate warnings",
             execution_time_ms=exec_ms,
         )


