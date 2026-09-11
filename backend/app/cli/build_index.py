"""CLI command: Build or rebuild the vector store index.

Usage:
    python -m backend.app.cli.build_index
"""

import sys
try:
    from backend.app.services.retrieval.vector_indexer import build_index
except ImportError:
    from app.services.retrieval.vector_indexer import build_index


def main():
    print("=" * 70)
    print("  ZYNTRIX BIS VECTOR INDEX BUILDER")
    print("=" * 70)
    res = build_index()
    print(f"Index Backend:   {res.get('backend')}")
    print(f"Collection:      {res.get('collection_name')}")
    print(f"Indexed Records: {res.get('indexed_count')}")
    print(f"Status:          {res.get('status')}")
    print("\nVector index build completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
