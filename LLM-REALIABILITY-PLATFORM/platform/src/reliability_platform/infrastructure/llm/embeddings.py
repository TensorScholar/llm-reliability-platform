 from __future__ import annotations

 from dataclasses import dataclass
 from typing import Iterable, List

 import numpy as np


 @dataclass(slots=True)
 class EmbeddingService:
     """Lightweight embedding service.

     This default implementation uses a fast hashing-based embedding to avoid
     heavyweight dependencies. It produces deterministic, low-cost vectors suitable
     for relative drift measurements. Swap with Sentence-Transformers in production.
     """

     dimension: int = 384
     normalize: bool = True

     async def embed(self, text: str) -> np.ndarray:
         """Embed a single string into a fixed-size vector.

         Args:
             text: Input text to embed

         Returns:
             Vector of shape (dimension,) as float32
         """

         return self._hash_embedding(text)

     async def embed_batch(self, texts: List[str]) -> np.ndarray:
         """Embed a batch of strings.

         Args:
             texts: List of input texts

         Returns:
             Matrix of shape (len(texts), dimension) as float32
         """

         if not texts:
             return np.zeros((0, self.dimension), dtype=np.float32)
         embeddings = [self._hash_embedding(t) for t in texts]
         return np.stack(embeddings, axis=0)

     def _hash_embedding(self, text: str) -> np.ndarray:
         tokens = self._tokenize(text)
         vec = np.zeros(self.dimension, dtype=np.float32)
         for tok in tokens:
             # Stable hash to bucket tokens into dimensions
             h = self._stable_hash(tok)
             idx = h % self.dimension
             # Signed contribution based on secondary hash bit
             sign = -1.0 if ((h >> 31) & 1) else 1.0
             vec[idx] += sign
         if self.normalize:
             norm = np.linalg.norm(vec) or 1.0
             vec /= norm
         return vec

     @staticmethod
     def _tokenize(text: str) -> Iterable[str]:
         return (t for t in text.lower().split() if t)

     @staticmethod
     def _stable_hash(token: str) -> int:
         # Python's built-in hash is salted per-process; use a stable alternative
         # implemented via FNV-1a 64-bit
         fnv_prime = 1099511628211
         hash_ = 1469598103934665603
         for b in token.encode("utf-8"):
             hash_ ^= b
             hash_ *= fnv_prime
             hash_ &= 0xFFFFFFFFFFFFFFFF  # keep 64-bit
         return hash_


