"""OpenDataLoader PDF Extraction Service.

Layer 1: Input Processing (OpenDataLoader AI-Ready Structured PDF Parser).
Enforces zero-hallucination, evidence-first provenance:
- Native Java-based high-accuracy layout analysis & reading-order reconstruction (XY-Cut++).
- Extracts semantic elements (headings, paragraphs, lists, tables) with exact bounding boxes.
- Outputs clean, structured Markdown and granular per-page JSON metadata.
- Seamless fallback support for in-memory streams and graceful degradation.
"""

import os
import io
import json
import shutil
import tempfile
import subprocess
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from backend.app.core.logging import logger

try:
    import opendataloader_pdf
    OPENDATALOADER_AVAILABLE = True
except ImportError:
    opendataloader_pdf = None
    OPENDATALOADER_AVAILABLE = False


def check_java_runtime() -> Dict[str, Any]:
    """Verify that a supported Java runtime (JDK 11+) is available on PATH."""
    java_cmd = shutil.which("java")
    if not java_cmd:
        return {"available": False, "version": None, "path": None}

    try:
        proc = subprocess.run(
            [java_cmd, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        version_output = proc.stderr or proc.stdout or ""
        first_line = version_output.strip().splitlines()[0] if version_output.strip() else "Java installed"
        return {"available": True, "version": first_line, "path": java_cmd}
    except Exception as exc:
        logger.warning(f"Failed to query java version: {exc}")
        return {"available": True, "version": "Unknown (query failed)", "path": java_cmd}


def is_opendataloader_ready() -> bool:
    """Return True if both opendataloader_pdf package and Java runtime are ready."""
    if not OPENDATALOADER_AVAILABLE:
        return False
    java_info = check_java_runtime()
    return bool(java_info.get("available"))


class OpenDataLoaderPageBlock(BaseModel):
    bbox: List[float] = Field(default_factory=list)
    text: str
    element_type: str = "paragraph"
    tag: Optional[str] = None
    id: Optional[int] = None


class OpenDataLoaderPage(BaseModel):
    page_number: int  # 1-indexed
    text: str
    markdown: str = ""
    char_count: int = 0
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    images_count: int = 0
    tables_count: int = 0
    extraction_method: str = "OPENDATALOADER_PDF"


class OpenDataLoaderResult(BaseModel):
    total_pages: int
    pages: List[OpenDataLoaderPage]
    markdown_content: str = ""
    title_metadata: Optional[str] = None
    author_metadata: Optional[str] = None
    source_name: str = "document.pdf"
    engine: str = "opendataloader-pdf"


def _flatten_kids(kids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Recursively flatten nested kids elements from OpenDataLoader JSON output."""
    flat = []
    for kid in kids:
        flat.append(kid)
        sub_kids = kid.get("kids") or kid.get("list items") or []
        if isinstance(sub_kids, list) and sub_kids:
            flat.extend(_flatten_kids(sub_kids))
    return flat


def _extract_content_string(item: Dict[str, Any]) -> str:
    """Extract clean string content from a single OpenDataLoader element."""
    content = item.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        # Table or nested text rows
        rows = []
        for r in content:
            if isinstance(r, list):
                rows.append(" | ".join(str(cell).strip() for cell in r if str(cell).strip()))
            elif isinstance(r, str):
                rows.append(r.strip())
        return "\n".join(rows).strip()
    return ""


def extract_with_opendataloader(
    file_input: Union[str, bytes],
    filename: Optional[str] = None,
    keep_temp: bool = False,
    use_struct_tree: bool = True,
    sanitize: bool = False,
    reading_order: Optional[str] = None,
    hybrid: Optional[str] = None,
) -> OpenDataLoaderResult:
    """Extract structured pages and reading-order markdown using OpenDataLoader PDF.
    
    Accepts either an absolute filesystem path or raw PDF bytes.
    Features enabled:
    - XY-Cut++ reading order & table border detection.
    - AI safety prompt injection protection (hidden/transparent text filtering).
    - Native Tagged PDF structure tree preservation when present.
    """
    if not is_opendataloader_ready():
        raise RuntimeError(
            "OpenDataLoader PDF is not available. Please ensure opendataloader-pdf is installed and Java 11+ is on PATH."
        )

    doc_name = filename or "document.pdf"
    temp_in_file = None
    temp_out_dir = tempfile.mkdtemp(prefix="zyntrix_odl_")

    try:
        # 1. Resolve input path
        if isinstance(file_input, bytes):
            if len(file_input) == 0:
                raise ValueError("PDF content is empty (0 bytes).")
            # Write to temporary file with .pdf extension
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(file_input)
                temp_in_file = f.name
            target_input_path = temp_in_file
        elif isinstance(file_input, str):
            doc_name = filename or os.path.basename(file_input)
            if not os.path.exists(file_input):
                raise FileNotFoundError(f"PDF file does not exist at {file_input}")
            if os.path.getsize(file_input) == 0:
                raise ValueError(f"PDF file '{doc_name}' is empty (0 bytes).")
            target_input_path = file_input
        else:
            raise TypeError(f"Unsupported file_input type: {type(file_input)}")

        # 2. Run OpenDataLoader conversion with advanced options
        convert_kwargs: Dict[str, Any] = {
            "input_path": target_input_path,
            "output_dir": temp_out_dir,
            "format": ["markdown", "json"],
            "quiet": True,
            "use_struct_tree": use_struct_tree,
            "sanitize": sanitize,
        }
        if reading_order:
            convert_kwargs["reading_order"] = reading_order
        if hybrid:
            convert_kwargs["hybrid"] = hybrid

        opendataloader_pdf.convert(**convert_kwargs)

        # 3. Read generated output files
        out_files = os.listdir(temp_out_dir)
        json_file = next((os.path.join(temp_out_dir, f) for f in out_files if f.endswith(".json")), None)
        md_file = next((os.path.join(temp_out_dir, f) for f in out_files if f.endswith(".md")), None)

        if not json_file:
            raise RuntimeError(f"OpenDataLoader PDF failed to generate structured JSON output in {temp_out_dir}")

        with open(json_file, "r", encoding="utf-8") as jf:
            parsed_json = json.load(jf)

        markdown_text = ""
        if md_file and os.path.exists(md_file):
            with open(md_file, "r", encoding="utf-8", errors="replace") as mf:
                markdown_text = mf.read()

        total_pages = int(parsed_json.get("number_pages") or parsed_json.get("number of pages") or 1)
        title_meta = parsed_json.get("title")
        author_meta = parsed_json.get("author")

        # 4. Group elements by page number
        all_kids = parsed_json.get("kids") or []
        flat_items = _flatten_kids(all_kids)

        pages_elements: Dict[int, List[Dict[str, Any]]] = {p: [] for p in range(1, total_pages + 1)}
        for item in flat_items:
            page_num = item.get("page number") or item.get("page_number") or 1
            if page_num not in pages_elements:
                pages_elements[page_num] = []
            pages_elements[page_num].append(item)

        # 5. Build Extracted Pages
        extracted_pages: List[OpenDataLoaderPage] = []
        for p_idx in range(1, total_pages + 1):
            items = pages_elements.get(p_idx, [])
            page_text_pieces = []
            structured_blocks = []
            images_count = 0
            tables_count = 0

            for el in items:
                el_type = el.get("type", "unknown")
                bbox = el.get("bounding box") or el.get("bbox") or []
                tag = el.get("pdfua_tag")
                el_id = el.get("id")

                if el_type == "image":
                    images_count += 1
                elif el_type == "table":
                    tables_count += 1

                content = _extract_content_string(el)
                if content:
                    page_text_pieces.append(content)
                    structured_blocks.append({
                        "bbox": bbox,
                        "text": content,
                        "block_type": el_type,
                        "tag": tag,
                        "id": el_id,
                    })

            page_full_text = "\n\n".join(page_text_pieces)
            extracted_pages.append(
                OpenDataLoaderPage(
                    page_number=p_idx,
                    text=page_full_text,
                    char_count=len(page_full_text),
                    blocks=structured_blocks,
                    images_count=images_count,
                    tables_count=tables_count,
                    extraction_method="OPENDATALOADER_PDF",
                )
            )

        logger.info(
            f"OpenDataLoader PDF successfully extracted {total_pages} pages from '{doc_name}' "
            f"({len(flat_items)} structured elements, {len(markdown_text)} chars markdown)"
        )

        return OpenDataLoaderResult(
            total_pages=total_pages,
            pages=extracted_pages,
            markdown_content=markdown_text,
            title_metadata=title_meta,
            author_metadata=author_meta,
            source_name=doc_name,
            engine="opendataloader-pdf",
        )

    finally:
        if not keep_temp:
            if temp_in_file and os.path.exists(temp_in_file):
                try:
                    os.remove(temp_in_file)
                except Exception:
                    pass
            if os.path.exists(temp_out_dir):
                try:
                    shutil.rmtree(temp_out_dir, ignore_errors=True)
                except Exception:
                    pass


def batch_extract_with_opendataloader(
    file_paths: List[str],
    output_dir: Optional[str] = None,
    use_struct_tree: bool = True,
    sanitize: bool = False,
) -> Dict[str, OpenDataLoaderResult]:
    """Batch process multiple PDF files in a single JVM call for maximal throughput.
    
    Spawns one single JVM process rather than repeatedly launching JVM instances.
    """
    if not is_opendataloader_ready():
        raise RuntimeError("OpenDataLoader PDF is not available.")
    
    if not file_paths:
        return {}

    temp_out_dir = output_dir or tempfile.mkdtemp(prefix="zyntrix_odl_batch_")
    results: Dict[str, OpenDataLoaderResult] = {}

    try:
        opendataloader_pdf.convert(
            input_path=file_paths,
            output_dir=temp_out_dir,
            format=["markdown", "json"],
            quiet=True,
            use_struct_tree=use_struct_tree,
            sanitize=sanitize,
        )

        for path in file_paths:
            base = os.path.splitext(os.path.basename(path))[0]
            json_file = os.path.join(temp_out_dir, f"{base}.json")
            md_file = os.path.join(temp_out_dir, f"{base}.md")

            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8") as jf:
                    parsed_json = json.load(jf)
                md_text = ""
                if os.path.exists(md_file):
                    with open(md_file, "r", encoding="utf-8", errors="replace") as mf:
                        md_text = mf.read()

                total_pages = int(parsed_json.get("number_pages") or parsed_json.get("number of pages") or 1)
                all_kids = parsed_json.get("kids") or []
                flat_items = _flatten_kids(all_kids)

                pages_elements: Dict[int, List[Dict[str, Any]]] = {p: [] for p in range(1, total_pages + 1)}
                for item in flat_items:
                    pnum = item.get("page number") or item.get("page_number") or 1
                    pages_elements.setdefault(pnum, []).append(item)

                extracted_pages = []
                for p_idx in range(1, total_pages + 1):
                    items = pages_elements.get(p_idx, [])
                    text_pieces = []
                    structured_blocks = []
                    img_cnt = sum(1 for el in items if el.get("type") == "image")
                    tbl_cnt = sum(1 for el in items if el.get("type") == "table")

                    for el in items:
                        c = _extract_content_string(el)
                        if c:
                            text_pieces.append(c)
                            structured_blocks.append({
                                "bbox": el.get("bounding box") or el.get("bbox") or [],
                                "text": c,
                                "block_type": el.get("type", "unknown"),
                                "tag": el.get("pdfua_tag"),
                                "id": el.get("id"),
                            })

                    p_text = "\n\n".join(text_pieces)
                    extracted_pages.append(
                        OpenDataLoaderPage(
                            page_number=p_idx,
                            text=p_text,
                            char_count=len(p_text),
                            blocks=structured_blocks,
                            images_count=img_cnt,
                            tables_count=tbl_cnt,
                            extraction_method="OPENDATALOADER_PDF",
                        )
                    )

                results[path] = OpenDataLoaderResult(
                    total_pages=total_pages,
                    pages=extracted_pages,
                    markdown_content=md_text,
                    title_metadata=parsed_json.get("title"),
                    author_metadata=parsed_json.get("author"),
                    source_name=os.path.basename(path),
                    engine="opendataloader-pdf",
                )
        return results

    finally:
        if not output_dir and os.path.exists(temp_out_dir):
            try:
                shutil.rmtree(temp_out_dir, ignore_errors=True)
            except Exception:
                pass


def auto_tag_pdf(input_path: str, output_dir: str) -> str:
    """Generate screen-reader-ready Tagged PDF from an untagged PDF (Well-Tagged PDF / veraPDF specification)."""
    if not is_opendataloader_ready():
        raise RuntimeError("OpenDataLoader PDF is not available.")
    
    opendataloader_pdf.convert(
        input_path=input_path,
        output_dir=output_dir,
        format="tagged-pdf",
        quiet=True,
    )
    base = os.path.splitext(os.path.basename(input_path))[0]
    candidate = os.path.join(output_dir, f"{base}.pdf")
    return candidate if os.path.exists(candidate) else output_dir

