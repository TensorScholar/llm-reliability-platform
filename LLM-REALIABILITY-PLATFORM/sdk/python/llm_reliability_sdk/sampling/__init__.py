 from __future__ import annotations

 import random


 class SamplingStrategy:
     def __init__(self, rate: float = 1.0, strategy: str = "uniform") -> None:
         self.rate = rate
         self.strategy = strategy

     def should_capture(self) -> bool:
         if self.rate >= 1.0:
             return True
         if self.rate <= 0.0:
             return False
         return random.random() < self.rate


