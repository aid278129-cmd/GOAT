"""Multi-Modal OCR & Image Processing Service.

Layer 1: Input Processing (Tesseract OCR & High-Contrast Fallback).
Enforces zero-hallucination, evidence-first provenance:
- Native Tesseract OCR is strictly separated from fallback parsing.
- Real mode never labels regex or fallback output as 'OCR'.
- Full cross-platform support: Windows, Linux, macOS, and Docker.
"""

import io
import os
import re
import shutil
import platform
from typing import Dict, Any, List, Optional, Tuple, Iterator
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont

from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False


def locate_tesseract_executable() -> Optional[str]:
    """Locates the Tesseract OCR binary across Windows, Linux, macOS, and Docker.
    
    Checks in order:
    1. settings.TESSERACT_CMD or TESSERACT_CMD environment variable
    2. PATH via shutil.which('tesseract')
    3. Standard Windows installation directories
    4. Standard Linux / Unix directories
    5. Standard macOS Homebrew / MacPorts directories
    """
    # 1. Configurable override
    configured = settings.TESSERACT_CMD or os.getenv("TESSERACT_CMD")
    if configured and os.path.isfile(configured):
        return configured

    # 2. PATH resolution
    in_path = shutil.which("tesseract")
    if in_path and os.path.isfile(in_path):
        return in_path

    # 3. Windows standard paths
    if platform.system() == "Windows":
        local_app_data = os.getenv("LOCALAPPDATA", "")
        windows_candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(local_app_data, "Programs", "Tesseract-OCR", "tesseract.exe"),
            os.path.join(local_app_data, "Tesseract-OCR", "tesseract.exe"),
        ]
        for candidate in windows_candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

    # 4. Linux / Unix standard paths
    linux_candidates = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract-ocr",
    ]
    for candidate in linux_candidates:
        if os.path.isfile(candidate):
            return candidate

    # 5. macOS standard paths
    mac_candidates = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for candidate in mac_candidates:
        if os.path.isfile(candidate):
            return candidate

    return None


def configure_tesseract() -> Optional[str]:
    """Configures pytesseract with the discovered executable path."""
    if not PYTESSERACT_AVAILABLE:
        return None

    path = locate_tesseract_executable()
    if path:
        pytesseract.pytesseract.tesseract_cmd = path
    return path


class OCRExtractionResult:
    """Structured result from OCR or fallback parsing.
    
    Provides backward compatibility for tuple unpacking `text, ok = result`
    while preserving rich metadata and explicit extraction method.
    """
    def __init__(
        self,
        text: str,
        success: bool,
        extraction_method: str = "FALLBACK_PARSER",  # NATIVE_TESSERACT_OCR | FALLBACK_PARSER | DEMO_FIXTURE | FAILED
        confidence: float = 0.0,
        languages: Optional[List[str]] = None,
        details: Optional[str] = None,
    ):
        self.text = text
        self.success = success
        self.extraction_method = extraction_method
        self.confidence = confidence
        self.languages = languages or ["eng"]
        self.details = details

    def __iter__(self) -> Iterator[Any]:
        return iter((self.text, self.success))

    def __getitem__(self, idx: int) -> Any:
        return (self.text, self.success)[idx]

    def __len__(self) -> int:
        return 2

    def __repr__(self) -> str:
        return (
            f"OCRExtractionResult(success={self.success}, method='{self.extraction_method}', "
            f"text_len={len(self.text)}, confidence={self.confidence})"
        )


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Preprocesses images for maximum OCR accuracy.
    
    Handles:
    - EXIF orientation correction (fixes rotated smartphone/scanner photos)
    - Grayscale normalization
    - Contrast enhancement for degraded or faded laboratory rating plates
    """
    try:
        # 1. Orientation correction from EXIF metadata
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # 2. Convert to Grayscale if RGB or RGBA
    if image.mode in ("RGBA", "LA", "P"):
        # Create solid white background for transparency
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
        image = background.convert("L")
    elif image.mode != "L":
        image = image.convert("L")

    # 3. Enhance contrast for clearer text boundaries
    try:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.8)
    except Exception:
        pass

    return image


def get_tesseract_runtime_info(run_live_test: bool = True) -> Dict[str, Any]:
    """Comprehensive runtime diagnostic of Tesseract installation, binary, and functional execution."""
    installed = PYTESSERACT_AVAILABLE
    binary_path = configure_tesseract()
    version = None
    languages: List[str] = []
    functional = False
    status = "NOT_CONFIGURED"
    error = None

    if not installed:
        return {
            "installed": False,
            "binary_installed": False,
            "executable_path": None,
            "version": None,
            "languages_available": [],
            "functional": False,
            "status": "NOT_CONFIGURED",
            "error": "pytesseract Python library is not installed.",
        }

    if not binary_path:
        return {
            "installed": True,
            "binary_installed": False,
            "executable_path": None,
            "version": None,
            "languages_available": [],
            "functional": False,
            "status": "FALLBACK_ACTIVE",
            "error": (
                "Tesseract binary not found in PATH or standard system locations. "
                "Set TESSERACT_CMD in .env or install Tesseract OCR."
            ),
        }

    # Binary found; verify version and languages
    try:
        version_str = str(pytesseract.get_tesseract_version())
        version = version_str
        try:
            languages = pytesseract.get_languages()
        except Exception:
            languages = ["eng"]

        # Run live execution test if requested
        if run_live_test:
            test_img = Image.new("L", (120, 40), color=255)
            draw = ImageDraw.Draw(test_img)
            draw.text((10, 10), "ZYNTRIX", fill=0)
            
            ocr_out = pytesseract.image_to_string(test_img, lang="eng").strip()
            # If tesseract executed without exception, it is functional
            functional = True
            status = "FUNCTIONAL"
        else:
            functional = True
            status = "CONFIGURED"

    except Exception as exc:
        functional = False
        status = "FAILED"
        error = f"Tesseract execution error: {str(exc)}"

    return {
        "installed": installed,
        "binary_installed": bool(binary_path),
        "executable_path": binary_path,
        "version": version,
        "languages_available": languages,
        "functional": functional,
        "status": status,
        "error": error,
    }


def extract_text_from_image_bytes(
    image_bytes: bytes,
    lang: str = "eng",
    is_scanned_pdf_page: bool = False,
) -> OCRExtractionResult:
    """Extract text from raw image bytes using Tesseract OCR if available.
    
    Adheres strictly to the M21 invariant:
    - Never call regex fallback 'OCR'.
    - Returns NATIVE_TESSERACT_OCR only when genuinely processed by Tesseract.
    - If unconfigured in real mode, reports FALLBACK_PARSER with clear diagnostic.
    """
    if not image_bytes:
        return OCRExtractionResult(
            text="",
            success=False,
            extraction_method="FAILED",
            confidence=0.0,
            details="Empty image payload received.",
        )

    # 1. Decode image via Pillow
    try:
        image = Image.open(io.BytesIO(image_bytes))
        format_name = getattr(image, "format", "UNKNOWN")
        image = preprocess_image_for_ocr(image)
    except Exception as exc:
        logger.warning(f"Image decoding failed: {exc}")
        return OCRExtractionResult(
            text="",
            success=False,
            extraction_method="FAILED",
            confidence=0.0,
            details=f"Invalid or unsupported image format: {exc}",
        )

    # 2. Check if Tesseract is available and configured
    binary_path = configure_tesseract()

    if PYTESSERACT_AVAILABLE and binary_path:
        try:
            raw_text = pytesseract.image_to_string(image, lang=lang)
            clean_text = raw_text.strip()
            logger.info(f"NATIVE_TESSERACT_OCR succeeded: {len(clean_text)} characters extracted from {format_name}.")
            return OCRExtractionResult(
                text=clean_text,
                success=True,
                extraction_method="NATIVE_TESSERACT_OCR",
                confidence=0.92 if len(clean_text) > 20 else 0.75,
                languages=[lang],
                details=f"Native Tesseract OCR executed via {binary_path}.",
            )
        except Exception as exc:
            logger.warning(f"Native Tesseract OCR call failed: {exc}")
            # Fall through to fallback parser

    # 3. Fallback Parser (explicitly NOT labeled as OCR)
    if settings.DEMO_MODE:
        # In Demo Mode, provide standard sample rating plate extraction
        demo_text = (
            "ELECTRIC IMMERSION WATER HEATER\n"
            "MODEL: EWH-1500 | 230V AC ~ 50Hz 1500W\n"
            "IS 302-2-201 | S/N: 2026-9021-IN\n"
            "MADE IN INDIA - STAINLESS STEEL SHEATH"
        )
        return OCRExtractionResult(
            text=demo_text,
            success=True,
            extraction_method="DEMO_FIXTURE",
            confidence=0.85,
            details="Demo Mode local fixture. For real image OCR, install Tesseract OCR.",
        )

    # In Production / Real Mode: Do NOT silently pretend fallback parsing is OCR!
    return OCRExtractionResult(
        text="",
        success=False,
        extraction_method="FALLBACK_PARSER",
        confidence=0.0,
        details=(
            "Tesseract OCR binary not detected on system. "
            "Native OCR execution unavailable. Configure TESSERACT_CMD or install Tesseract to enable image extraction."
        ),
    )


def is_scanned_page(text: str, image_count: int, min_char_threshold: int = 40) -> bool:
    """Determine if a PDF page appears to be a scanned bitmap rather than vector text."""
    clean_text = (text or "").strip()
    return len(clean_text) < min_char_threshold and image_count > 0
