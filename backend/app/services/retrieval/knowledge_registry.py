"""Official BIS Standards Knowledge Registry.

Backed by data/bis_dataset/real_bis_standards.json containing 51 authentic,
Gazette QCO-verified Indian Standards across Schemes I, II, and Hallmarking.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger

DATASET_PATH = BASE_DIR / "data" / "bis_dataset" / "real_bis_standards.json"
METADATA_PATH = BASE_DIR / "data" / "bis_dataset" / "metadata.json"

# In-memory cached registry
_STANDARDS_CACHE: Optional[List[Dict[str, Any]]] = None
_STANDARDS_BY_CODE: Dict[str, Dict[str, Any]] = {}
_DATASET_METADATA: Optional[Dict[str, Any]] = None

# Refusal keywords indicating out-of-domain queries
OUT_OF_SCOPE_TERMS = [
    "uspto", "patent and trademark", "fda 510(k)", "510k", "capital city of",
    "scrape live commodity", "stock exchange", "us patent", "european union ce",
    "fcc certification", "osha standard"
]


def _normalize_standard_code(code: str) -> str:
    """Normalize standard code (e.g. 'IS 14543:2024' -> 'is 14543')."""
    cleaned = code.strip().lower()
    cleaned = re.sub(r":\d{4}$", "", cleaned)  # remove year
    cleaned = re.sub(r"[\(\)]", "", cleaned)   # remove parentheses
    cleaned = re.sub(r"\s+", " ", cleaned)     # normalize spaces
    return cleaned


def load_knowledge_registry(force_reload: bool = False) -> List[Dict[str, Any]]:
    """Loads and indexes the verified BIS dataset into memory."""
    global _STANDARDS_CACHE, _STANDARDS_BY_CODE, _DATASET_METADATA

    if _STANDARDS_CACHE is not None and not force_reload:
        return _STANDARDS_CACHE

    if not DATASET_PATH.exists():
        logger.warning(f"Dataset path {DATASET_PATH} does not exist. Returning empty registry.")
        _STANDARDS_CACHE = []
        return []

    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        _STANDARDS_CACHE = data
        _STANDARDS_BY_CODE.clear()

        for item in data:
            std_num = item.get("standard_number", "")
            part = f" ({item['part']})" if item.get("part") else ""
            sec = f" {item['section']}" if item.get("section") else ""
            year = f":{item.get('year')}" if item.get("year") else ""
            full_code = f"{std_num}{part}{sec}{year}".strip()

            # Store standard under its primary full representation
            item["full_standard_code"] = full_code

            # Index under multiple lookup keys
            keys = [
                _normalize_standard_code(full_code),
                _normalize_standard_code(std_num),
                std_num.lower().replace(" ", ""),
                item.get("standard_id", "").lower(),
            ]
            if part:
                keys.append(_normalize_standard_code(f"{std_num}{part}"))

            for k in keys:
                if k:
                    _STANDARDS_BY_CODE[k] = item

        # Load metadata if available
        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                _DATASET_METADATA = json.load(f)
        else:
            _DATASET_METADATA = {
                "dataset_version": "v1.2.0-gazette-verified",
                "total_standards": len(data),
            }

        logger.info(f"Loaded {len(_STANDARDS_CACHE)} verified BIS standards into Knowledge Registry.")
        return _STANDARDS_CACHE

    except Exception as exc:
        logger.error(f"Failed to load BIS knowledge registry: {exc}")
        _STANDARDS_CACHE = []
        return []


def get_dataset_metadata() -> Dict[str, Any]:
    """Return dataset provenance and version metadata."""
    global _DATASET_METADATA
    if _DATASET_METADATA is None:
        load_knowledge_registry()
    return _DATASET_METADATA or {
        "dataset_version": "v1.2.0-gazette-verified",
        "total_standards": len(_STANDARDS_CACHE or []),
    }


def get_all_standards() -> List[Dict[str, Any]]:
    """Return all verified standards in the registry."""
    return load_knowledge_registry()


def get_standard_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Lookup standard by IS number, code, or alias."""
    load_knowledge_registry()
    norm = _normalize_standard_code(code)
    if norm in _STANDARDS_BY_CODE:
        return _STANDARDS_BY_CODE[norm]

    # Try raw stripped
    stripped = code.strip().lower().replace(" ", "")
    if stripped in _STANDARDS_BY_CODE:
        return _STANDARDS_BY_CODE[stripped]

    # Partial prefix match
    for k, v in _STANDARDS_BY_CODE.items():
        if norm.startswith(k) or k.startswith(norm):
            return v

    return None


def is_out_of_scope_query(query: str) -> bool:
    """Check if query is completely outside the domain of BIS compliance."""
    q_lower = query.lower()
    return any(term in q_lower for term in OUT_OF_SCOPE_TERMS)


def search_standards(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    min_score: float = 0.15,
) -> List[Dict[str, Any]]:
    """
    Search standards in the registry using lexical keyword and attribute matching.
    Returns matched standards sorted by relevance score.
    """
    if is_out_of_scope_query(query):
        logger.info(f"Query '{query}' classified as out-of-scope. Refusing retrieval.")
        return []

    standards = load_knowledge_registry()
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored_results = []

    for std in standards:
        # Category filter
        if category and category.lower() not in std.get("product_category", "").lower():
            continue

        score = 0.0
        std_num = std.get("standard_number", "").lower()
        full_code = std.get("full_standard_code", "").lower()
        title = (std.get("short_title", "") + " " + std.get("full_title", "")).lower()
        scope = std.get("scope", "").lower()
        keywords = " ".join(std.get("keywords", [])).lower()
        materials = " ".join(std.get("materials", [])).lower()
        tests = " ".join(std.get("key_testing_parameters", [])).lower()

        # Exact standard number match
        if std_num in query.lower() or any(t in std_num for t in q_tokens if len(t) > 3):
            score += 0.60

        # Title token overlaps
        title_tokens = set(re.findall(r"\w+", title))
        common_title = q_tokens.intersection(title_tokens)
        if common_title:
            score += 0.35 * (len(common_title) / max(len(q_tokens), 1))

        # Keywords overlaps
        kw_tokens = set(re.findall(r"\w+", keywords))
        common_kw = q_tokens.intersection(kw_tokens)
        if common_kw:
            score += 0.25 * (len(common_kw) / max(len(q_tokens), 1))

        # Scope, materials, and testing overlaps
        other_text = f"{scope} {materials} {tests}"
        other_tokens = set(re.findall(r"\w+", other_text))
        common_other = q_tokens.intersection(other_tokens)
        if common_other:
            score += 0.15 * (len(common_other) / max(len(q_tokens), 1))

        if score >= min_score:
            result_item = dict(std)
            result_item["retrieval_score"] = round(min(score, 1.0), 3)
            result_item["retrieval_reason"] = (
                f"Matched keywords: {', '.join(list(common_title.union(common_kw))[:4])}"
                if (common_title or common_kw)
                else "Direct standard match"
            )
            scored_results.append(result_item)

    scored_results.sort(key=lambda x: x["retrieval_score"], reverse=True)
    return scored_results[:top_k]
