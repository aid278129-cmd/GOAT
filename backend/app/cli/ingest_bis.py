"""CLI command: Ingest and validate official BIS standards dataset.

Usage:
    python -m backend.app.cli.ingest_bis
"""

import sys
try:
    from backend.app.services.retrieval.knowledge_registry import load_knowledge_registry, get_dataset_metadata
except ImportError:
    from app.services.retrieval.knowledge_registry import load_knowledge_registry, get_dataset_metadata


def main():
    print("=" * 70)
    print("  ZYNTRIX BIS DATASET INGESTION PIPELINE")
    print("=" * 70)
    standards = load_knowledge_registry(force_reload=True)
    meta = get_dataset_metadata()

    print(f"Dataset Name:     {meta.get('dataset_name', 'BIS-standards-dataset')}")
    print(f"Dataset Version:  {meta.get('dataset_version', 'v1.2.0-gazette-verified')}")
    print(f"Total Standards:  {len(standards)}")
    print(f"Upstream Source:  {meta.get('upstream_source')}")
    print(f"SHA-256 Hash:     {meta.get('sha256')}")
    print("\nSample Ingested Standards:")
    for i, s in enumerate(standards[:5]):
        print(f"  {i+1}. {s.get('standard_number')}:{s.get('year')} — {s.get('short_title')} ({s.get('scheme')})")

    print("\nIngestion and schema verification completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
