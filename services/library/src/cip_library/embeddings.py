import hashlib
import re
from collections.abc import Sequence
from itertools import pairwise
from typing import Protocol

import numpy as np

from cip_library.config import Settings

TOKEN = re.compile(r"[a-záéíóúñü0-9]+")


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class HashingEmbedder:
    def __init__(self, dimension: int = 1024) -> None:
        self.dimension = dimension
        self.name = f"hashing-{dimension}"

    def _features(self, text: str) -> list[str]:
        tokens = TOKEN.findall(text.lower())
        return tokens + [f"{left} {right}" for left, right in pairwise(tokens)]

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            for feature in self._features(text):
                value = int.from_bytes(hashlib.blake2b(feature.encode(), digest_size=8).digest(), "little")
                matrix[row, value % self.dimension] += 1.0 if value >> 63 else -1.0
        return normalize_rows(matrix)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_documents([text])[0]


class FastEmbedEmbedder:
    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)
        self.name = model_name

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return normalize_rows(np.array(list(self._model.passage_embed(list(texts))), dtype=np.float32))

    def embed_query(self, text: str) -> np.ndarray:
        return normalize_rows(np.array(list(self._model.query_embed(text)), dtype=np.float32))[0]


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedder == "fastembed":
        return FastEmbedEmbedder(settings.embedding_model)
    return HashingEmbedder()
