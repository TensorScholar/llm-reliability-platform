 from __future__ import annotations

 from dataclasses import dataclass
 from typing import Generic, Optional, TypeVar


 T = TypeVar("T")


 @dataclass(frozen=True)
 class Result(Generic[T]):
     value: Optional[T] = None
     error: Optional[str] = None

     @property
     def is_ok(self) -> bool:
         return self.error is None


