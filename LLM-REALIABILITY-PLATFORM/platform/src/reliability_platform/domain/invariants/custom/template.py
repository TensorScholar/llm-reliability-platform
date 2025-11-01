 from __future__ import annotations

 import asyncio

 from ..base import AbstractInvariant, InvariantCategory, InvariantContext, InvariantMetadata
 from ...models.validation import ValidationResult, ValidationStatus


 class CustomTemplateInvariant(AbstractInvariant):
     """Template invariant example for users to extend."""

     @property
     def metadata(self) -> InvariantMetadata:
         return InvariantMetadata(
             id="custom.template",
             name="Custom Template",
             description="User-defined template invariant",
             category=InvariantCategory.CUSTOM,
         )

     async def validate(self, context: InvariantContext) -> ValidationResult:
         start = asyncio.get_event_loop().time()
         ms = int((asyncio.get_event_loop().time() - start) * 1000)
         return self._create_result(
             context=context, status=ValidationStatus.PASSED, message="Template pass", execution_time_ms=ms
         )


