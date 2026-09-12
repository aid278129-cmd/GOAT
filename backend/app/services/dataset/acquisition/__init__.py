"""Official BIS Source Acquisition & Local Corpus Engine.

Milestone M25.1A implementation:
- Whitelisted official BIS domains crawler and discovery
- Conservative downloader with legal access control
- 12 separate source collections in data/bis/
- Strict cryptographic SHA-256 provenance tracking
- Non-automatic verification ('ACQUIRED' != 'VERIFIED')
- Immutable corpus snapshots and change detection
"""

from backend.app.services.dataset.acquisition.config import (
    BIS_CORPUS_ROOT,
    CORPUS_DIRS,
    OFFICIAL_BIS_DOMAINS,
    OFFICIAL_SEED_URLS,
    is_official_bis_domain,
    ensure_corpus_directories,
)
from backend.app.services.dataset.acquisition.models import (
    AcquisitionState,
    SourceType,
    SourceManifest,
    DiscoveredResource,
    CorpusSnapshotManifest,
    CorpusIntegrityReport,
    VerificationReport,
    VerificationIssue,
)
from backend.app.services.dataset.acquisition.discovery import OfficialBISDiscoverer
from backend.app.services.dataset.acquisition.downloader import (
    DocumentDownloader,
    AcquisitionDownloadResult,
)
from backend.app.services.dataset.acquisition.processor import DocumentProcessor
from backend.app.services.dataset.acquisition.extractor import (
    MetadataExtractor,
    ExtractedStandardMetadata,
    ExtractedQCOMetadata,
    ExtractedLabRecord,
)
from backend.app.services.dataset.acquisition.verifier import CorpusVerifier
from backend.app.services.dataset.acquisition.corpus_manager import CorpusManager

__all__ = [
    "BIS_CORPUS_ROOT",
    "CORPUS_DIRS",
    "OFFICIAL_BIS_DOMAINS",
    "OFFICIAL_SEED_URLS",
    "is_official_bis_domain",
    "ensure_corpus_directories",
    "AcquisitionState",
    "SourceType",
    "SourceManifest",
    "DiscoveredResource",
    "CorpusSnapshotManifest",
    "CorpusIntegrityReport",
    "VerificationReport",
    "VerificationIssue",
    "OfficialBISDiscoverer",
    "DocumentDownloader",
    "AcquisitionDownloadResult",
    "DocumentProcessor",
    "MetadataExtractor",
    "ExtractedStandardMetadata",
    "ExtractedQCOMetadata",
    "ExtractedLabRecord",
    "CorpusVerifier",
    "CorpusManager",
]
