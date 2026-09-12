"""Official BIS Crawler and Discovery Engine.

Discovers publicly accessible official BIS regulatory sources:
- Official BIS Web URLs (whitelisted domains only)
- CRS Compulsory Registration product listings from official BIS records
- Gazette notifications & established standards from official Gazette schedules
- Classifies each resource into one of 12 distinct categories.
"""

import os
import re
import ssl
import urllib.request
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.config import (
    OFFICIAL_SEED_URLS,
    USER_AGENT,
    REQUEST_TIMEOUT_SECONDS,
    is_official_bis_domain,
)
from backend.app.services.dataset.acquisition.models import (
    SourceType,
    DiscoveredResource,
)

# SSL context for official government websites
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def classify_resource_by_content(
    title: str, url: str, link_text: str = ""
) -> Tuple[SourceType, str]:
    """Classifies a resource into SourceType and Local Corpus Category."""
    t_lower = f"{title} {link_text} {url}".lower()

    if "amendment" in t_lower or "amdt" in t_lower:
        return SourceType.BIS_AMENDMENT, "AMENDMENTS"
    elif "revised" in t_lower or "revision" in t_lower or "supersed" in t_lower:
        return SourceType.BIS_REVISION, "REVISIONS"
    elif re.search(r"\bsti\b", t_lower) or "scheme of testing" in t_lower or "testing and inspection" in t_lower:
        return SourceType.BIS_SIT, "SCHEME_OF_TESTING_AND_INSPECTION"
    elif "product manual" in t_lower or "quality manual" in t_lower or "hm_manual" in t_lower:
        return SourceType.BIS_PRODUCT_MANUAL, "PRODUCT_MANUALS"
    elif "guideline" in t_lower or "guidance" in t_lower or "procedure" in t_lower:
        return SourceType.BIS_PRODUCT_GUIDELINE, "PRODUCT_SPECIFIC_GUIDELINES"
    elif "registration scheme" in t_lower or "mark scheme" in t_lower or re.search(r"\bscheme\s*[-–]\s*(?:i|ii|iv|x|\d+)\b", t_lower):
        return SourceType.BIS_SCHEME, "CERTIFICATION_SCHEMES"
    elif "qco" in t_lower or "quality control order" in t_lower:
        return SourceType.BIS_QCO, "QCO"
    elif "gazette" in t_lower or "notification" in t_lower or ("order" in t_lower and "qco" not in t_lower):
        return SourceType.BIS_GAZETTE, "GAZETTE"
    elif "lab" in t_lower or "laboratory" in t_lower or "lrs" in t_lower or "lims" in t_lower:
        return SourceType.BIS_LABORATORY, "LABORATORIES"
    elif "licence" in t_lower or "license" in t_lower or "refiner" in t_lower or "jeweller" in t_lower:
        return SourceType.BIS_LICENCE, "LICENCES"
    elif "scheme" in t_lower or "hallmarking" in t_lower:
        return SourceType.BIS_SCHEME, "CERTIFICATION_SCHEMES"
    elif re.search(r"is\s+\d+", t_lower):
        return SourceType.BIS_STANDARD, "STANDARDS"
    else:
        return SourceType.BIS_CATALOG, "STANDARDS"


class OfficialBISDiscoverer:
    """Discovers publicly available official BIS documents and catalog data."""

    def __init__(self, seed_urls: Optional[List[str]] = None):
        self.seed_urls = seed_urls or OFFICIAL_SEED_URLS
        self.discovered: Dict[str, DiscoveredResource] = {}
        self.seen_urls: Set[str] = set()

    def fetch_html(self, url: str) -> Optional[str]:
        """Politely fetch HTML from an official BIS URL."""
        if not is_official_bis_domain(url):
            logger.warning(f"Rejected non-official URL during discovery: {url}")
            return None
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            )
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Discovery fetch failed for {url}: {e}")
            return None

    def discover_from_web(self, max_pages: int = 5) -> List[DiscoveredResource]:
        """Crawl official BIS configured URLs and extract publicly accessible documents."""
        newly_discovered: List[DiscoveredResource] = []

        for idx, page_url in enumerate(self.seed_urls[:max_pages]):
            if page_url in self.seen_urls:
                continue
            self.seen_urls.add(page_url)

            html = self.fetch_html(page_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            page_title = soup.title.string.strip() if soup.title else page_url

            # Find all links on the page
            for a in soup.find_all("a", href=True):
                raw_href = a["href"].strip()
                if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:"):
                    continue

                full_url = urljoin(page_url, raw_href)
                link_text = a.get_text(strip=True) or "Untitled Document"

                # Reject non-official domains
                if not is_official_bis_domain(full_url):
                    continue

                # Check if it is a downloadable document or specific resource
                is_pdf = full_url.lower().endswith(".pdf")
                is_specific_page = any(
                    k in full_url.lower()
                    for k in ["scheme", "guideline", "order", "qco", "lab", "product"]
                )

                if is_pdf or is_specific_page:
                    if full_url in self.discovered:
                        continue

                    src_type, category = classify_resource_by_content(
                        title=link_text, url=full_url, link_text=link_text
                    )

                    # Extract standard number if present in text
                    std_match = re.search(r"IS\s+\d+(?:[\s\-:\(\)A-Za-z0-9]+)?", link_text)
                    std_num = std_match.group(0).strip() if std_match else None

                    res = DiscoveredResource(
                        url=full_url,
                        title=link_text,
                        source_type=src_type,
                        category=category,
                        standard_number=std_num,
                        parent_url=page_url,
                        is_downloadable=is_pdf,
                        notes=f"Discovered on {page_title}",
                    )
                    self.discovered[full_url] = res
                    newly_discovered.append(res)

        return newly_discovered

    def discover_from_crs_text(self, filepath: Optional[Path] = None) -> List[DiscoveredResource]:
        """Ingests official BIS CRS product listings from Products Covered.txt."""
        path = filepath or (BASE_DIR / "Products Covered.txt")
        if not path.exists():
            return []

        results: List[DiscoveredResource] = []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Pattern matching Sl. No. -> Product -> IS No -> Date
            # Products Covered format:
            # <sl_no>\n\n<product_name>\n\n<is_no>\n\n<date>
            pattern = re.compile(
                r"(\d+)\s*\n+\s*([A-Z0-9\s/(),\"\-\&]+?)\s*\n+\s*(IS\s+[\d\(\)\s:\-A-Za-z\&/]+?)\s*\n+\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                re.MULTILINE,
            )

            for match in pattern.finditer(content):
                sl_no, product, is_no, qco_date = match.groups()
                clean_is = is_no.strip()
                clean_prod = product.strip()
                clean_date = qco_date.strip()
                resource_url = f"https://www.crsbis.in/BIS/products-covered.do#sl-{sl_no}"

                if resource_url in self.discovered:
                    continue

                res = DiscoveredResource(
                    url=resource_url,
                    title=f"CRS Mandatory Registration: {clean_prod} ({clean_is})",
                    source_type=SourceType.BIS_QCO,
                    category="QCO",
                    standard_number=clean_is,
                    is_downloadable=False,
                    notes=f"QCO Implementation Date: {clean_date}. Product: {clean_prod}",
                )
                self.discovered[resource_url] = res
                results.append(res)
        except Exception as e:
            logger.error(f"Error reading CRS products: {e}")

        return results

    def discover_from_local_gazette_sources(self) -> List[DiscoveredResource]:
        """Ingests authentic BIS Gazette notifications present in Source Data/Gazette/."""
        gazette_dir = BASE_DIR / "Source Data" / "Gazette"
        results: List[DiscoveredResource] = []
        if not gazette_dir.exists():
            return results

        for p in gazette_dir.glob("*.pdf"):
            filename = p.name
            url = f"https://www.bis.gov.in/gazette/{filename}"
            if url in self.discovered:
                continue

            if "HQ-PUB" in filename or "PUB-BIS" in filename:
                src_type = SourceType.BIS_GAZETTE
                category = "GAZETTE"
                title = f"Gazette of India BIS Notification ({filename})"
            else:
                src_type = SourceType.BIS_STANDARD
                category = "STANDARDS"
                title = f"Standard Document ({filename})"

            res = DiscoveredResource(
                url=url,
                title=title,
                source_type=src_type,
                category=category,
                is_downloadable=True,
                notes=f"Local authentic official Gazette asset: {p}",
            )
            self.discovered[url] = res
            results.append(res)

        return results

    def run_discovery(self) -> List[DiscoveredResource]:
        """Run full discovery across web and official local BIS assets."""
        web_res = self.discover_from_web()
        crs_res = self.discover_from_crs_text()
        local_res = self.discover_from_local_gazette_sources()
        total = web_res + crs_res + local_res
        logger.info(f"Discovery completed: {len(total)} official BIS resources identified.")
        return list(self.discovered.values())
