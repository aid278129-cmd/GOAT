from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class RerankerProvider(ABC):
    """Abstract interface for reranking candidate retrieved clauses."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass


class ExactMatchAndRelevanceReranker(RerankerProvider):
    """Lightweight deterministic cross-matching reranker.
    
    Promotes candidates that:
    1. Contain exact clause number or technical standard matches.
    2. Contain exact multi-word term matches from the query.
    3. Retain high combined lexical + semantic signals.
    """

    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        q_lower = query.lower()
        q_tokens = [w for w in q_lower.split() if len(w) > 2]

        reranked = []
        for cand in candidates:
            text = (cand.get("text_content") or "").lower()
            title = (cand.get("clause_title") or "").lower()
            clause_num = (cand.get("clause_number") or "").lower()
            std_num = (cand.get("standard_number") or "").lower()

            bonus = 0.0
            # 1. Exact clause or standard number mention
            if clause_num and clause_num in q_lower:
                bonus += 0.5
            if std_num and std_num in q_lower:
                bonus += 0.4

            # 2. Exact title token matches
            title_hits = sum(1 for t in q_tokens if t in title)
            bonus += min(0.3, title_hits * 0.1)

            # 3. Requirement code match
            for req in cand.get("requirements", []):
                req_code = req.code.lower() if hasattr(req, "code") else str(req.get("code", "")).lower()
                if req_code in q_lower:
                    bonus += 0.4

            initial_score = cand.get("hybrid_score", cand.get("similarity_score", 0.0))
            cand["rerank_score"] = round(initial_score + bonus, 4)
            cand["final_score"] = cand["rerank_score"]
            reranked.append(cand)

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked


default_reranker = ExactMatchAndRelevanceReranker()
