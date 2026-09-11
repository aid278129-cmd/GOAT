import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter


class BM25LexicalIndex:
    """In-memory BM25 lexical index for fast clause text scoring.
    
    Adheres to Okapi BM25 ranking algorithm:
    - k1 = 1.5, b = 0.75
    - Term frequency normalization by document length
    - Inverse Document Frequency (IDF) smoothing
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lengths: List[int] = []
        self.doc_ids: List[str] = []
        self.term_freqs: List[Counter] = []
        self.doc_freqs: Counter = Counter()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text) if len(w) > 1]

    def index_documents(self, documents: List[Tuple[str, str]]) -> None:
        """Index a list of (doc_id, text) tuples."""
        self.doc_ids = []
        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = Counter()
        self.corpus_size = len(documents)

        total_len = 0
        for doc_id, text in documents:
            tokens = self._tokenize(text)
            doc_len = len(tokens)
            self.doc_ids.append(doc_id)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf = Counter(tokens)
            self.term_freqs.append(tf)
            for t in tf.keys():
                self.doc_freqs[t] += 1

        self.avg_doc_len = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0

    def score(self, query: str) -> List[Tuple[str, float]]:
        """Score all indexed documents against query and return list of (doc_id, score)."""
        if self.corpus_size == 0 or self.avg_doc_len == 0:
            return []

        q_tokens = self._tokenize(query)
        scores: List[Tuple[str, float]] = []

        for idx, doc_id in enumerate(self.doc_ids):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            tf = self.term_freqs[idx]

            for term in q_tokens:
                if term not in tf:
                    continue
                df = self.doc_freqs.get(term, 0)
                # Smoothed Robertson-Spärck Jones IDF
                idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
                f = tf[term]
                tf_norm = (f * (self.k1 + 1.0)) / (f + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len)))
                score += idf * tf_norm

            if score > 0.0:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
