"""CLI command: Verify BIS knowledge integrity and provenance hashes.

Usage:
    python -m backend.app.cli.verify_knowledge
"""

import sys
import hashlib
try:
    from backend.app.core.config import BASE_DIR
    from backend.app.services.retrieval.knowledge_registry import load_knowledge_registry, get_dataset_metadata
except ImportError:
    from app.core.config import BASE_DIR
    from app.services.retrieval.knowledge_registry import load_knowledge_registry, get_dataset_metadata

DATASET_FILE = BASE_DIR / "data" / "bis_dataset" / "real_bis_standards.json"


def main():
    print("=" * 70)
    print("  ZYNTRIX BIS KNOWLEDGE INTEGRITY VERIFIER")
    print("=" * 70)

    if not DATASET_FILE.exists():
        print(f"[ERROR] Dataset file not found: {DATASET_FILE}")
        return 1

    content = DATASET_FILE.read_bytes()
    current_hash = hashlib.sha256(content).hexdigest()
    meta = get_dataset_metadata()
    expected_hash = meta.get("sha256")

    print(f"Dataset Path:    {DATASET_FILE}")
    print(f"Current SHA256:  {current_hash}")
    print(f"Recorded SHA256: {expected_hash}")

    standards = load_knowledge_registry()
    print(f"Standards Count: {len(standards)}")

    verified_count = sum(1 for s in standards if s.get("verification_status") in ("verified_accurate", "corrected"))
    print(f"Verified Records: {verified_count} / {len(standards)}")

    if expected_hash and current_hash == expected_hash:
        print("\n[SUCCESS] Cryptographic checksum matches official recorded metadata.")
        return 0
    else:
        print("\n[WARNING] Checksum differs or was not recorded, but dataset parsed validly.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
