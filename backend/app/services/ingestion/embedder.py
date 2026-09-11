import os
import math
import hashlib
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class EmbeddingProvider:
    """Abstract Base Class for text embedding generation."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class DeterministicLocalEmbeddingProvider(EmbeddingProvider):
    """Deterministic, normalized pseudo-semantic embedding generator for offline development & testing.

    Generates a reproducible 384-dimensional dense float vector based on word n-grams and hashing.
    """

    def __init__(self, dimension: int = 384):
        super().__init__(dimension=dimension)
        self.model_name = "deterministic-384-local"

    def embed_query(self, text: str) -> List[float]:
        """Alias for embed_text matching standard retrieval interfaces."""
        return self.embed_text(text)

    def embed_text(self, text: str) -> List[float]:
        clean_text = text.lower().strip()
        if not clean_text:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        words = clean_text.split()

        for word in words:
            # Hash word into bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 4) % 2 == 0 else -1.0
            weight = math.log1p(len(word))
            vector[idx] += sign * weight

        # Also add bigrams for local phrase semantics
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.sha1(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 3) % 2 == 0 else -1.0
            vector[idx] += sign * 1.5

        # L2-normalize vector
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two normalized vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


# Singleton default provider for local ingestion & search
default_embedding_provider = DeterministicLocalEmbeddingProvider(dimension=384)
