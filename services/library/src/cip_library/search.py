import re
from collections import defaultdict

import numpy as np
from cip_contracts import Passage, SearchRequest

from cip_library.embeddings import Embedder
from cip_library.store import LibraryStore

RRF_K = 60
CANDIDATES = 40
STOPWORDS = frozenset(
    "the and for with from that this into under over are was were has have its their about "
    "los las del por para con una unos sobre entre como que sus".split()
)
WORD = re.compile(r"\w+")


def to_match_query(query: str) -> str:
    terms = [term for term in WORD.findall(query.lower()) if len(term) > 2 and term not in STOPWORDS]
    return " OR ".join(f'"{term}"' for term in dict.fromkeys(terms))


class HybridSearcher:
    def __init__(self, store: LibraryStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._cache: dict[str, tuple[list[str], np.ndarray]] = {}

    def invalidate(self, library_id: str) -> None:
        self._cache.pop(library_id, None)

    def _vectors(self, library_id: str) -> tuple[list[str], np.ndarray]:
        if library_id not in self._cache:
            self._cache[library_id] = self._store.vectors(library_id)
        return self._cache[library_id]

    def _semantic(self, library_id: str, query: str) -> list[str]:
        passage_ids, matrix = self._vectors(library_id)
        if not passage_ids:
            return []
        scores = matrix @ self._embedder.embed_query(query)
        best = np.argsort(-scores)[:CANDIDATES]
        return [passage_ids[index] for index in best if scores[index] > 0]

    def _lexical(self, library_id: str, query: str) -> list[str]:
        match_query = to_match_query(query)
        return self._store.lexical_search(library_id, match_query, CANDIDATES) if match_query else []

    def search(self, library_id: str, request: SearchRequest) -> list[Passage]:
        fused: dict[str, float] = defaultdict(float)
        for query in request.queries:
            for ranking in (self._lexical(library_id, query), self._semantic(library_id, query)):
                for rank, passage_id in enumerate(ranking):
                    fused[passage_id] += 1 / (RRF_K + rank + 1)
        ranked = sorted(fused, key=fused.__getitem__, reverse=True)
        per_paper: dict[str, int] = defaultdict(int)
        results: list[Passage] = []
        for passage in self._store.passages(ranked, request.year_from):
            if per_paper[passage.paper_id] >= request.per_paper:
                continue
            per_paper[passage.paper_id] += 1
            results.append(passage.model_copy(update={"score": round(fused[passage.passage_id], 5)}))
            if len(results) == request.top_k:
                break
        return results
