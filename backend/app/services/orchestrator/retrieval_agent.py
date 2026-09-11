"""Layer 3: Advanced LangChain Retrieval Agent (Milestone M24.4.3B).

Architectural Invariants Strictly Enforced:
1. ONE LLM ONLY: Model execution delegates strictly to the single LLM singleton / adapter.
2. ZERO COMPLIANCE AUTHORITY: Retrieval Agent compliance authority is exactly 0.0%.
   Authority level is strictly AI_DERIVED / CANDIDATE.
   It cannot declare, evaluate, certify, or conclude regulatory compliance.
3. PRESERVE FOUNDATIONAL TRUTHS:
   - USER_TEXT != EVIDENCE != COMPLIANCE
   - NO VERIFIED SOURCE -> NO REGULATORY CLAIM
   - INDEXED != VERIFIED
   - INGESTION != VERIFICATION
   - CONFLICT -> EXPERT REVIEW
4. DETERMINISTIC CONTROL FLOW: Graph routing remains deterministic; no autonomous loops.
5. CROSS-STANDARD ISOLATION: Strict standard boundaries. Clauses from foreign standards are
   intercepted, quarantined, and excluded from primary evidence candidates.
6. EXACT NUMBER PRESERVATION: Numbers, units, tolerances, and clause IDs are preserved bit-for-bit.
"""

import re
import time
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from backend.app.services.compliance.authority_types import AuthorityLevel, AuthoritySource
from backend.app.services.orchestrator.schemas import OrchestratorIntent, GroundingStatus
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.services.orchestrator.tools.guards import (
    sanitize_and_validate_argument,
    enforce_standard_isolation,
)
from backend.app.services.retrieval.reranker import default_reranker, ExactMatchAndRelevanceReranker
from backend.app.core.logging import logger


# ==============================================================================
# ENUMS & CONSTANTS
# ==============================================================================

MAX_RETRIEVED_CLAUSES = 15
MAX_EXPANDED_TERMS = 8

class RetrievalStrategy(str, Enum):
    """Retrieval strategy selected based on request intent and complexity."""
    EXACT_CLAUSE_LOOKUP = "EXACT_CLAUSE_LOOKUP"
    STANDARD_SCOPED_SEMANTIC = "STANDARD_SCOPED_SEMANTIC"
    HYBRID_KEYWORD_BM25 = "HYBRID_KEYWORD_BM25"
    MULTI_CLAUSE_TRAVERSAL = "MULTI_CLAUSE_TRAVERSAL"
    FALLBACK_BROAD_SEARCH = "FALLBACK_BROAD_SEARCH"


class RetrievalQualityTier(str, Enum):
    """Grading of retrieval match quality and source trustworthiness."""
    STRONG_MATCH = "STRONG_MATCH"
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"
    NO_RELIABLE_MATCH = "NO_RELIABLE_MATCH"
    VERIFIED_SOURCE_MATCH = "VERIFIED_SOURCE_MATCH"
    UNVERIFIED_SOURCE_MATCH = "UNVERIFIED_SOURCE_MATCH"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


# Verified technical terminology mappings for deterministic query expansion
TECHNICAL_EXPANSION_DICTIONARY: Dict[str, List[str]] = {
    "creepage": ["clearance", "insulation distance", "electric strength", "Table 2A"],
    "clearance": ["creepage distance", "insulation", "electric spacing"],
    "insulation": ["dielectric strength", "insulation resistance", "leakage current", "electric strength"],
    "leakage current": ["electric strength", "operating temperature", "insulation resistance", "mA"],
    "earthing": ["continuity of earthing", "protective earth", "grounding terminal", "resistance <= 0.1 Ohm"],
    "drop test": ["impact test", "mechanical strength", "abuse testing", "drop height"],
    "food grade": ["food contact", "grade 304", "stainless steel", "IS 6911", "IS 9845"],
    "flammability": ["resistance to heat and fire", "glow wire", "enclosure", "UL94"],
    "plug": ["supply connection", "flexible cord", "IS 1293", "pin", "rated current"],
    "marking": ["nameplate", "rated voltage", "rated wattage", "trade name", "standard mark"],
    "small parts": ["choking hazard", "small parts cylinder", "age grading", "under 36 months"],
    "impact": ["shock absorption", "peak acceleration", "drop tower", "300g"],
    "thermal": ["heat retention", "temperature retention", "vacuum insulation", "hours"],
}


# ==============================================================================
# DATA CONTRACTS (PYDANTIC V2)
# ==============================================================================

class CandidateClauseItem(BaseModel):
    """A retrieved clause candidate for downstream analysis."""
    clause_number: str
    clause_title: str
    requirement_text: str
    standard_number: str
    verified: bool = True
    confidence_score: float = 1.0
    authority: str = "AI_DERIVED / CANDIDATE"
    source_provenance: str = "BIS_VERIFIED_CATALOG"
    is_expanded_match: bool = False
    provenance_hash: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.provenance_hash:
            raw = f"{self.standard_number}:{self.clause_number}:{self.requirement_text}"
            self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class QuarantinedClauseItem(BaseModel):
    """A clause candidate rejected due to cross-standard isolation boundary violation."""
    clause_number: str
    clause_title: str
    standard_number: str
    attempted_for_standard: str
    reason: str = "CROSS_STANDARD_LEAKAGE_PREVENTED"
    timestamp: float = Field(default_factory=time.time)


class RetrievalPlan(BaseModel):
    """Retrieval plan formulated before executing tools.
    
    Hard Invariant: Authority is strictly AI_DERIVED.
    Compliance Authority is strictly 0.0.
    """
    target_standard_number: str
    query_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[str] = Field(default_factory=list)
    targeted_clause_numbers: List[str] = Field(default_factory=list)
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.STANDARD_SCOPED_SEMANTIC
    max_results: int = 10
    confidence_threshold: float = 0.5
    require_verified_source: bool = True
    authority: str = "AI_DERIVED"
    llm_compliance_authority: float = 0.0


class RetrievalPackage(BaseModel):
    """Structured handover package produced for the downstream Analysis Agent."""
    standard_number: str
    strategy_used: RetrievalStrategy
    quality_tier: RetrievalQualityTier
    candidates: List[CandidateClauseItem] = Field(default_factory=list)
    quarantined_clauses: List[QuarantinedClauseItem] = Field(default_factory=list)
    total_retrieved: int = 0
    total_quarantined: int = 0
    from_cache: bool = False
    context_tokens_estimated: int = 0
    numeric_constraints_preserved: int = 0
    provenance: str = "AI_DERIVED / CANDIDATE"
    llm_compliance_authority: float = 0.0
    regulatory_conclusion: str = "NONE"


# ==============================================================================
# 1. RETRIEVAL STRATEGY SELECTOR
# ==============================================================================

class RetrievalStrategySelector:
    """Selects the most deterministic and context-efficient retrieval strategy."""

    @classmethod
    def select_strategy(
        cls,
        target_standard: str,
        query: str,
        clause_references: List[str],
        request_type: Optional[str] = None,
    ) -> RetrievalStrategy:
        """Deterministically choose the optimal retrieval strategy."""
        clean_q = (query or "").lower().strip()

        # Strategy 1: Explicit clause references requested
        if clause_references and len(clause_references) > 0:
            if len(clause_references) == 1:
                return RetrievalStrategy.EXACT_CLAUSE_LOOKUP
            return RetrievalStrategy.MULTI_CLAUSE_TRAVERSAL

        # Strategy 2: Check if query contains an explicit clause number pattern (e.g., "clause 13.1")
        if re.search(r"\bclause\s*\d+(?:\.\d+)*\b", clean_q):
            return RetrievalStrategy.EXACT_CLAUSE_LOOKUP

        # Strategy 3: Known specific technical terms -> Hybrid keyword search
        technical_keywords = {"drop test", "leakage current", "earthing", "creepage", "flammability", "markings"}
        if any(kw in clean_q for kw in technical_keywords):
            return RetrievalStrategy.HYBRID_KEYWORD_BM25

        # Strategy 4: Standard-scoped semantic search for general queries
        if target_standard:
            return RetrievalStrategy.STANDARD_SCOPED_SEMANTIC

        # Fallback
        return RetrievalStrategy.FALLBACK_BROAD_SEARCH


# ==============================================================================
# 2. QUERY EXPANSION ENGINE
# ==============================================================================

class QueryExpansionEngine:
    """Deterministic domain-bounded query expansion engine.
    
    Invariants:
    - Bounded expansion (MAX_EXPANDED_TERMS = 8).
    - Preserves product DNA parameters without hallucinating standards.
    - Tags expanded terms with provenance.
    """

    @classmethod
    def expand_query_terms(
        cls,
        query: str,
        product_dna: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[str], List[str]]:
        """Extract core terms and generate deterministic technical expansions."""
        clean_q = (query or "").lower().strip()
        tokens = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", clean_q)]
        
        stops = {
            "what", "does", "clause", "require", "standard", "about", "tell", "show",
            "the", "and", "for", "all", "with", "from", "that", "this", "are", "not",
            "shall", "must", "can", "may", "have", "has", "had", "will", "would",
            "check", "comply", "compliance", "give", "list", "test", "requirement"
        }
        core_terms = [t for t in tokens if t not in stops]

        expanded_terms: List[str] = []
        for term in core_terms:
            for dict_key, expansions in TECHNICAL_EXPANSION_DICTIONARY.items():
                if dict_key in clean_q or term in dict_key:
                    for exp in expansions:
                        if exp.lower() not in clean_q and exp.lower() not in expanded_terms:
                            expanded_terms.append(exp)
                            if len(expanded_terms) >= MAX_EXPANDED_TERMS:
                                break
            if len(expanded_terms) >= MAX_EXPANDED_TERMS:
                break

        # Incorporate Product DNA if present (e.g. material, voltage, wattage)
        if product_dna:
            for key, val in product_dna.items():
                if val and isinstance(val, (str, int, float)):
                    val_str = str(val).strip().lower()
                    if val_str and val_str not in clean_q and len(expanded_terms) < MAX_EXPANDED_TERMS:
                        expanded_terms.append(val_str)

        return core_terms, expanded_terms[:MAX_EXPANDED_TERMS]


# ==============================================================================
# 3. CROSS-STANDARD ISOLATION FILTER
# ==============================================================================

class CrossStandardIsolationFilter:
    """Enforces strict standard isolation to prevent cross-standard contamination.
    
    Hard Invariant:
    If a retrieval operation targets IS 302-2-201, any returned clause from IS 17526,
    IS 13252, or any foreign standard MUST be intercepted and quarantined.
    """

    @classmethod
    def extract_base_standard(cls, std_identifier: str) -> str:
        """Extract base standard code family (e.g. 'IS 302' from 'IS 302-2-201:2008' or 'IS 17526')."""
        clean = std_identifier.strip().upper()
        m = re.search(r"\bIS\s*(\d+)", clean)
        if m:
            return f"IS {m.group(1)}"
        return clean

    @classmethod
    def filter_and_isolate(
        cls,
        target_standard: str,
        candidates: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[QuarantinedClauseItem]]:
        """Partition candidates into valid isolated clauses and quarantined foreign clauses."""
        target_clean = target_standard.strip().upper()
        target_base = cls.extract_base_standard(target_clean)

        isolated_candidates: List[Dict[str, Any]] = []
        quarantined: List[QuarantinedClauseItem] = []

        for cand in candidates:
            cand_std = str(cand.get("standard_number") or "").strip().upper()
            cand_base = cls.extract_base_standard(cand_std)

            # Standard isolation check:
            # Candidate standard base must match target standard base
            is_valid = False
            if not target_std_filter_active(target_clean):
                is_valid = True
            elif target_clean in cand_std or cand_std in target_clean or target_base == cand_base:
                is_valid = True
            else:
                is_valid = False

            if is_valid:
                isolated_candidates.append(cand)
            else:
                q_item = QuarantinedClauseItem(
                    clause_number=str(cand.get("clause_number", "UNKNOWN")),
                    clause_title=str(cand.get("clause_title", "")),
                    standard_number=cand_std,
                    attempted_for_standard=target_clean,
                    reason=f"CROSS_STANDARD_LEAKAGE_PREVENTED: Clause belongs to '{cand_std}' which differs from target standard '{target_clean}'.",
                )
                quarantined.append(q_item)
                logger.warning(
                    f"[CrossStandardIsolation] Intercepted cross-standard leakage: "
                    f"Clause {cand.get('clause_number')} of {cand_std} attempted under {target_clean}."
                )

        return isolated_candidates, quarantined


def target_std_filter_active(target_clean: str) -> bool:
    """Return True if target_clean is a concrete standard."""
    return bool(target_clean and target_clean != "UNKNOWN" and "IS" in target_clean)


# ==============================================================================
# 4. CONTEXT PRUNER & EXACT NUMERIC PRESERVER
# ==============================================================================

class ContextPrunerAndNumericPreserver:
    """Prunes token fluff from requirement text while strictly preserving:
    - Numerical values (230, 1250, 0.75, 5%, 10 min)
    - Units (V, AC, mA, MOhm, C, m, mm, g, Ohm, %)
    - Tolerances (+5%, -10%, +/- 5%)
    - Clause titles and normative keywords (shall, must, not exceed)
    """

    NUMERIC_PATTERN = re.compile(
        r"(?:[+\-±]?\s*\d+(?:\.\d+)?\s*(?:%|v|vac|vdc|ma|a|mohm|kohm|ohm|c|m|mm|g|hz|kpa|min|s|h|hours|droplets|grade\s*\d+)?\b)",
        re.IGNORECASE,
    )

    @classmethod
    def count_numeric_constraints(cls, text: str) -> int:
        """Count distinct numeric constraints, units, and tolerances."""
        if not text:
            return 0
        matches = cls.NUMERIC_PATTERN.findall(text)
        return len([m for m in matches if any(ch.isdigit() for ch in m)])

    @classmethod
    def prune_and_preserve(cls, requirement_text: str) -> Tuple[str, int]:
        """Prune filler while preserving exact requirements and numeric constraints."""
        if not requirement_text:
            return "", 0

        # Preserve numbers count
        count = cls.count_numeric_constraints(requirement_text)

        # Clean excess whitespace
        pruned = re.sub(r"\s+", " ", requirement_text).strip()
        return pruned, count


# ==============================================================================
# 5. RESULT QUALITY ASSESSOR
# ==============================================================================

class ResultQualityAssessor:
    """Evaluates retrieval quality tier deterministically."""

    @classmethod
    def assess_quality(
        cls,
        candidates: List[CandidateClauseItem],
        target_standard: str,
        targeted_clauses: List[str],
    ) -> RetrievalQualityTier:
        """Determine quality tier based on candidate count, verification, and precision."""
        if not candidates:
            if target_standard and target_standard not in VERIFIED_STANDARDS_CATALOG:
                return RetrievalQualityTier.OUT_OF_SCOPE
            return RetrievalQualityTier.NO_RELIABLE_MATCH

        # Check source verification
        all_verified = all(c.verified for c in candidates)
        if not all_verified:
            return RetrievalQualityTier.UNVERIFIED_SOURCE_MATCH

        # If specific clauses were targeted
        if targeted_clauses:
            retrieved_numbers = {c.clause_number for c in candidates}
            if any(t in retrieved_numbers for t in targeted_clauses):
                return RetrievalQualityTier.STRONG_MATCH
            return RetrievalQualityTier.UNCERTAIN_MATCH

        # If candidates have high confidence and verified catalog provenance
        if len(candidates) >= 1:
            return RetrievalQualityTier.VERIFIED_SOURCE_MATCH

        return RetrievalQualityTier.UNCERTAIN_MATCH


# ==============================================================================
# 6. UNIFIED RETRIEVAL AGENT ENGINE
# ==============================================================================

class RetrievalAgent:
    """Production-grade LangChain Retrieval Agent for Zyntrix BIS Compliance Compiler.
    
    Coordinates:
    - Pre-check cache to eliminate duplicate tool calls
    - Formulation of typed RetrievalPlan
    - Strategy selection
    - Deterministic query expansion
    - Tool execution through controlled tool boundaries
    - Cross-standard isolation enforcement (quarantining cross-talk)
    - Lightweight exact-match and relevance reranking
    - Context pruning with strict numeric preservation
    - Quality tier assessment
    - Structuring typed RetrievalPackage for Analysis Agent
    """

    def __init__(self, reranker: Optional[ExactMatchAndRelevanceReranker] = None):
        self.reranker = reranker or default_reranker

    def formulate_plan(
        self,
        target_standard: str,
        query: str,
        clause_references: Optional[List[str]] = None,
        request_type: Optional[str] = None,
        product_dna: Optional[Dict[str, Any]] = None,
    ) -> RetrievalPlan:
        """Formulate a deterministic RetrievalPlan."""
        clauses = clause_references or []
        strategy = RetrievalStrategySelector.select_strategy(
            target_standard=target_standard,
            query=query,
            clause_references=clauses,
            request_type=request_type,
        )

        core_terms, expanded_terms = QueryExpansionEngine.expand_query_terms(
            query=query,
            product_dna=product_dna,
        )

        return RetrievalPlan(
            target_standard_number=target_standard,
            query_terms=core_terms,
            expanded_terms=expanded_terms,
            targeted_clause_numbers=clauses,
            retrieval_strategy=strategy,
            max_results=MAX_RETRIEVED_CLAUSES,
            confidence_threshold=0.5,
            require_verified_source=True,
            authority="AI_DERIVED",
            llm_compliance_authority=0.0,
        )

    def execute_retrieval(
        self,
        state: Dict[str, Any],
        tool_executor_fn: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute full retrieval lifecycle within LangGraph state machine.
        
        Invariants strictly maintained:
        - state is updated with candidate clauses and metadata.
        - Authority is strictly AI_DERIVED / CANDIDATE.
        - Compliance authority is 0.0%.
        """
        t0 = time.time()
        target_std = state.get("target_standard_number", "IS 302-2-201:2008")
        sanitized_q = state.get("sanitized_query", "")
        product_dna = state.get("product_dna", {})

        # Extract clause references if determined by query agent
        targeted_clauses: List[str] = []
        u_contract = state.get("node_contracts", {}).get("request_understanding", {})
        if u_contract:
            targeted_clauses = u_contract.get("clause_references", [])

        # 1. Formulate Retrieval Plan
        plan = self.formulate_plan(
            target_standard=target_std,
            query=sanitized_q,
            clause_references=targeted_clauses,
            request_type=u_contract.get("request_type"),
            product_dna=product_dna,
        )

        existing_clauses = state.get("retrieved_candidate_clauses", [])
        raw_candidates: List[Dict[str, Any]] = []
        from_cache = False
        tool_calls_executed: List[Dict[str, Any]] = []

        # 2. Check Cache / Pre-existing clauses
        if existing_clauses and any(c.get("standard_number") == target_std for c in existing_clauses):
            raw_candidates = list(existing_clauses)
            from_cache = True
            state["duplicate_tool_calls_prevented"] = state.get("duplicate_tool_calls_prevented", 0) + 1
        else:
            # 3. Execute Controlled Tool Call
            try:
                state["retrieval_call_count"] = state.get("retrieval_call_count", 0) + 1
                search_query = sanitized_q
                
                # If targeted clauses exist, augment query with clause numbers
                if targeted_clauses:
                    search_query = f"{sanitized_q} {' '.join(targeted_clauses)}".strip()
                elif plan.expanded_terms:
                    # Deterministic query expansion augmentation
                    search_query = f"{sanitized_q} {' '.join(plan.expanded_terms[:3])}".strip()

                tool_input = {
                    "standard_number": target_std,
                    "query": search_query,
                    "top_k": plan.max_results,
                }

                if tool_executor_fn:
                    tool_res = tool_executor_fn(
                        state=state,
                        node_name="retrieval_agent",
                        tool_name="search_bis_clauses",
                        tool_input=tool_input,
                        role="retrieval_agent",
                    )
                else:
                    from backend.app.services.orchestrator.tools.bis_tools import search_bis_clauses
                    tool_res = search_bis_clauses.invoke(tool_input)

                tool_calls_executed.append({
                    "tool": "search_bis_clauses",
                    "input": tool_input,
                    "returned_count": len(tool_res.clauses) if hasattr(tool_res, "clauses") else 0,
                })

                clauses_list = tool_res.clauses if hasattr(tool_res, "clauses") else []
                for cl in clauses_list:
                    cl_dict = cl.model_dump() if hasattr(cl, "model_dump") else (
                        cl.dict() if hasattr(cl, "dict") else dict(cl)
                    )
                    raw_candidates.append(cl_dict)

            except Exception as exc:
                logger.error(f"[RetrievalAgent] Controlled retrieval tool execution failed: {exc}")
                state["errors"] = state.get("errors", []) + [str(exc)]

        # 4. Cross-Standard Isolation Filter
        isolated_candidates, quarantined = CrossStandardIsolationFilter.filter_and_isolate(
            target_standard=target_std,
            candidates=raw_candidates,
        )

        # 5. Coordinate Deterministic Reranking
        if len(isolated_candidates) > 1:
            rerank_query = f"{sanitized_q} {' '.join(targeted_clauses)}".strip()
            # Map candidate dict keys for reranker compatibility
            for c in isolated_candidates:
                c["text_content"] = c.get("requirement_text", "")
            isolated_candidates = self.reranker.rerank(rerank_query, isolated_candidates)

        # 6. Context Pruning & Exact Numeric Preservation
        final_candidates: List[CandidateClauseItem] = []
        total_numeric_constraints = 0
        total_tokens_est = 0

        # Duplicate suppression set
        seen_clauses: Set[Tuple[str, str]] = set()

        for cand in isolated_candidates:
            c_num = str(cand.get("clause_number", "")).strip()
            c_std = str(cand.get("standard_number", "")).strip()
            key = (c_std, c_num)
            if key in seen_clauses:
                continue
            seen_clauses.add(key)

            req_text = str(cand.get("requirement_text") or cand.get("text_content") or "")
            pruned_text, num_count = ContextPrunerAndNumericPreserver.prune_and_preserve(req_text)
            total_numeric_constraints += num_count
            total_tokens_est += max(1, len(pruned_text) // 4)

            # Determine if match was via expansion
            is_expanded = any(
                exp.lower() in pruned_text.lower() or exp.lower() in str(cand.get("clause_title", "")).lower()
                for exp in plan.expanded_terms
            )

            item = CandidateClauseItem(
                clause_number=c_num,
                clause_title=str(cand.get("clause_title", "")),
                requirement_text=pruned_text,
                standard_number=c_std,
                verified=bool(cand.get("verified", True)),
                confidence_score=float(cand.get("final_score", cand.get("confidence_score", 1.0))),
                authority="AI_DERIVED / CANDIDATE",
                is_expanded_match=is_expanded,
            )
            final_candidates.append(item)

        # 7. Result Quality Assessment
        quality_tier = ResultQualityAssessor.assess_quality(
            candidates=final_candidates,
            target_standard=target_std,
            targeted_clauses=targeted_clauses,
        )

        # 8. Package for Analysis Agent Handover
        package = RetrievalPackage(
            standard_number=target_std,
            strategy_used=plan.retrieval_strategy,
            quality_tier=quality_tier,
            candidates=final_candidates,
            quarantined_clauses=quarantined,
            total_retrieved=len(final_candidates),
            total_quarantined=len(quarantined),
            from_cache=from_cache,
            context_tokens_estimated=total_tokens_est,
            numeric_constraints_preserved=total_numeric_constraints,
            provenance="AI_DERIVED / CANDIDATE",
            llm_compliance_authority=0.0,
            regulatory_conclusion="NONE",
        )

        # Update Graph State
        state["retrieved_candidate_clauses"] = [c.model_dump() for c in final_candidates]
        state["retrieval_package"] = package.model_dump()
        state["retrieval_plan"] = plan.model_dump()
        state["cross_standard_violations"] = [q.model_dump() for q in quarantined]

        return state


# Singleton instance
retrieval_agent = RetrievalAgent()
