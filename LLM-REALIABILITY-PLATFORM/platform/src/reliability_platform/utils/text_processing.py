 from __future__ import annotations

 import re
 from typing import Iterable


 def tokenize_simple(text: str) -> list[str]:
     return [t for t in re.split(r"\W+", text.lower()) if t]


 def sentence_count(text: str) -> int:
     return len([s for s in text.split(".") if s.strip()])


