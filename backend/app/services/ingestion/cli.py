import asyncio
import sys
import argparse
from pathlib import Path

# Add repo root to sys.path if not present
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.database.session import AsyncSessionLocal
from backend.app.services.ingestion.pipeline import ingest_standard_document


async def ingest_async(args):
    file_path = args.file
    print(f"[Zyntrix BIS Ingestion CLI] Ingesting: {file_path}")

    async with AsyncSessionLocal() as session:
        try:
            summary = await ingest_standard_document(
                db=session,
                file_path=file_path,
                standard_number_override=args.standard,
                standard_title_override=args.title,
                is_verified=args.verified,
                source_type=args.source_type,
                source_url=args.source_url,
                publisher=args.publisher,
            )
            print("========================================")
            print("  INGESTION COMPLETE (M1.5 PIPELINE)")
            print("========================================")
            print(f"Standard:        {summary.standard_number} - {summary.standard_title}")
            print(f"Document ID:     {summary.document_id}")
            print(f"File SHA-256:    {summary.file_hash}")
            print(f"Pages Processed: {summary.total_pages}")
            print(f"Clauses Indexed: {summary.clauses_ingested}")
            print(f"Requirements:    {summary.requirements_ingested}")
            print(f"Trust Status:    {summary.verification_status}")
            print(f"Ingestion State: {summary.ingestion_status}")
            print("========================================")
            if summary.verification_status != "VERIFIED":
                print("")
                print("  NOTE: Document is INDEXED but NOT VERIFIED.")
                print("  Use --verified flag only for confirmed authoritative sources.")
                print("")
        except Exception as exc:
            print(f"[ERROR] Ingestion failed: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Zyntrix BIS Document Ingestion CLI (M1.5)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a BIS Standard PDF or Document")
    ingest_parser.add_argument("file", type=str, help="Path to standard PDF file")
    ingest_parser.add_argument("--standard", type=str, default=None, help="Standard number (e.g. IS 17526:2021)")
    ingest_parser.add_argument("--title", type=str, default=None, help="Standard title override")
    ingest_parser.add_argument(
        "--verified", action="store_true", default=False,
        help="Mark as VERIFIED (default is REQUIRES_REVIEW). Only use for confirmed authoritative sources."
    )
    ingest_parser.add_argument(
        "--source-type", type=str, default="USER_PROVIDED",
        choices=["BIS_OFFICIAL", "GOVERNMENT_OFFICIAL", "SECONDARY", "USER_PROVIDED", "OTHER"],
        help="Source authority type (default: USER_PROVIDED)"
    )
    ingest_parser.add_argument("--source-url", type=str, default=None, help="Source URL for provenance tracking")
    ingest_parser.add_argument("--publisher", type=str, default=None, help="Publisher name")

    # Register subcommand (controlled import)
    register_parser = subparsers.add_parser("register", help="Register a source and document without full ingestion")
    register_parser.add_argument("file", type=str, help="Path to document file")
    register_parser.add_argument("--standard", type=str, default=None, help="Standard number")
    register_parser.add_argument("--title", type=str, default=None, help="Document title")
    register_parser.add_argument(
        "--source-type", type=str, default="USER_PROVIDED",
        choices=["BIS_OFFICIAL", "GOVERNMENT_OFFICIAL", "SECONDARY", "USER_PROVIDED", "OTHER"],
    )
    register_parser.add_argument("--source-url", type=str, default=None)
    register_parser.add_argument("--publisher", type=str, default=None)

    args = parser.parse_args()
    if args.command == "ingest":
        asyncio.run(ingest_async(args))
    elif args.command == "register":
        asyncio.run(register_async(args))


async def register_async(args):
    """Register a document and source without running full ingestion pipeline."""
    from backend.app.services.ingestion.document_loader import calculate_file_sha256
    from backend.app.services.ingestion.pipeline import register_source
    import os

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    file_hash = calculate_file_sha256(file_path)
    print(f"[Zyntrix] Registering document: {file_path}")
    print(f"[Zyntrix] SHA-256: {file_hash}")

    async with AsyncSessionLocal() as session:
        source = await register_source(
            db=session,
            name=args.standard or os.path.basename(file_path),
            publisher=args.publisher or "Unknown",
            source_type=args.source_type,
            authority_level="AUTHORITATIVE" if args.source_type == "BIS_OFFICIAL" else "UNVERIFIED",
            source_url=args.source_url,
            access_method="cli_import",
        )
        print(f"Source registered: {source.id} (type: {source.source_type}, authority: {source.authority_level})")
        print(f"Document SHA-256: {file_hash}")
        print(f"Status: DISCOVERED / UNVERIFIED (requires full ingestion + verification)")


if __name__ == "__main__":
    main()
