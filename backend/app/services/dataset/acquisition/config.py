"""Configuration and Domain Policy for Official BIS Source Acquisition.

Enforces:
1. Strict restriction to official Bureau of Indian Standards (BIS) domains only.
2. Canonical directory structures under data/bis/.
3. Polite rate-limiting, non-aggressive concurrency, and conservative backoff.
4. Absolute prohibition against bypassing logins, paywalls, or access restrictions.
"""

from pathlib import Path
from typing import Set, Dict, Any
from urllib.parse import urlparse
from backend.app.core.config import BASE_DIR

# Root directory for BIS local corpus
BIS_CORPUS_ROOT = BASE_DIR / "data" / "bis"

# 12 Required Local Corpus Directories + Governance Folders
CORPUS_DIRS = {
    "STANDARDS": BIS_CORPUS_ROOT / "standards",
    "PRODUCT_MANUALS": BIS_CORPUS_ROOT / "product_manuals",
    "SCHEME_OF_TESTING_AND_INSPECTION": BIS_CORPUS_ROOT / "sit",
    "PRODUCT_SPECIFIC_GUIDELINES": BIS_CORPUS_ROOT / "product_guidelines",
    "QCO": BIS_CORPUS_ROOT / "qco",
    "GAZETTE": BIS_CORPUS_ROOT / "gazette",
    "AMENDMENTS": BIS_CORPUS_ROOT / "amendments",
    "REVISIONS": BIS_CORPUS_ROOT / "revisions",
    "NORMATIVE_REFERENCES": BIS_CORPUS_ROOT / "normative_references",
    "CERTIFICATION_SCHEMES": BIS_CORPUS_ROOT / "schemes",
    "LABORATORIES": BIS_CORPUS_ROOT / "laboratories",
    "LICENCES": BIS_CORPUS_ROOT / "licences",
    "MANIFESTS": BIS_CORPUS_ROOT / "manifests",
    "SNAPSHOTS": BIS_CORPUS_ROOT / "snapshots",
    "ACQUISITION_LOGS": BIS_CORPUS_ROOT / "acquisition_logs",
}

# Whitelist of Authoritative Official BIS Domains
OFFICIAL_BIS_DOMAINS: Set[str] = {
    "bis.gov.in",
    "www.bis.gov.in",
    "standardsbis.bsbedge.com",
    "crsbis.in",
    "www.crsbis.in",
    "lims.bis.gov.in",
    "services.bis.gov.in",
    "manakonline.in",
    "huid.manakonline.in",
}

# Configured Official BIS Seed URLs
OFFICIAL_SEED_URLS = [
    "https://www.bis.gov.in/",
    "https://www.bis.gov.in/product-certification/product-specific-guideline/?lang=en",
    "https://www.bis.gov.in/know-your-standard/",
    "https://standardsbis.bsbedge.com/",
    "https://www.bis.gov.in/product-certification/?lang=en",
    "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en",
    "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en",
    "https://www.bis.gov.in/product-certification/product-certification-process/?lang=en",
]

# Client & Crawler Settings
REQUEST_TIMEOUT_SECONDS: int = 15
REQUEST_DELAY_SECONDS: float = 0.5
MAX_RETRIES: int = 2
USER_AGENT: str = "ZyntrixComplianceCompiler/1.0 (Official BIS Regulatory Source Acquisition; Respectful Crawler)"
MAX_DOCUMENT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB limit

# File magic bytes
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "html": (b"<!DOCTYPE", b"<html", b"<HTML"),
    "json": (b"{", b"["),
}


def is_official_bis_domain(url: str) -> bool:
    """Validate whether a URL belongs to the strictly whitelisted official BIS domains."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        # Direct match or subdomain of an official BIS domain
        return any(
            hostname == d or hostname.endswith("." + d)
            for d in OFFICIAL_BIS_DOMAINS
        )
    except Exception:
        return False


def ensure_corpus_directories() -> None:
    """Ensure all 12 category directories plus governance directories exist."""
    for d in CORPUS_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
