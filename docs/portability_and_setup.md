# Zyntrix Multi-Modal Layer 1 Setup & Portability Guide

This guide documents installation, environment configuration, binary discovery, and container deployment for **Layer 1: Multi-Modal Ingestion** across Windows, Linux, macOS, and Docker.

---

## 1. Architecture & Technology Matrix

| Modality | Technology Engine | Offline/Local Capability | Cloud Dependency | Fallback Behavior |
|---|---|---|---|---|
| **PDF** | PyMuPDF (`fitz`) | 100% Offline | None | Text extraction + layout bounding boxes |
| **Image / OCR** | Tesseract OCR + Pillow | 100% Offline | None | High-contrast regex & metadata parsing (`FALLBACK_PARSER`) |
| **Voice** | OpenAI Whisper / Faster-Whisper | Offline model or Cloud API | OpenAI API (Optional) | `VOICE_CLOUD_NOT_CONFIGURED` in Real Mode; `DEMO_FIXTURE` in Demo Mode |
| **BOM** | Python Tabular Engine | 100% Offline | None | Disambiguated duplicate resolution & parametric unit normalizer |
| **Manual Spec**| Pydantic Schema Pipeline | 100% Offline | None | Real-time requirement gap detection |

---

## 2. Platform Installation Guides

### A. Windows 10 / 11

#### 1. Tesseract OCR Installation
- **Option 1 (Winget - Recommended)**:
  ```powershell
  winget install --id UB-Mannheim.TesseractOCR
  ```
  Default installation directory:
  `C:\Program Files\Tesseract-OCR\tesseract.exe`

- **Option 2 (Manual Installer)**:
  1. Download installer from: `https://github.com/UB-Mannheim/tesseract/wiki`
  2. Run `tesseract-ocr-w64-setup-v5.x.exe` and select your language packs (e.g., English, Hindi).
  3. The Zyntrix auto-discovery engine automatically scans `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  4. Alternatively, configure in `backend/.env`:
     ```ini
     TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

#### 2. Whisper Speech-to-Text Setup
- **Cloud Mode (Recommended)**:
  Add your API key to `backend/.env`:
  ```ini
  OPENAI_API_KEY="sk-proj-your-actual-api-key"
  ```
- **Local Offline Engine**:
  ```powershell
  pip install openai-whisper
  # Requires ffmpeg on PATH (e.g., winget install Gyan.FFmpeg)
  ```

---

### B. Linux (Ubuntu / Debian / RHEL)

#### 1. System Packages Installation
```bash
sudo apt-get update && sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    ffmpeg \
    libmupdf-dev \
    python3-pip
```

#### 2. Python Dependencies
```bash
pip install -r backend/requirements.txt
```

#### 3. Verification
```bash
which tesseract
# Outputs: /usr/bin/tesseract
tesseract --version
```
Zyntrix automatically discovers `/usr/bin/tesseract` and activates `NATIVE_TESSERACT_OCR`.

---

### C. macOS (Apple Silicon / Intel)

#### 1. Homebrew Installation
```bash
brew install tesseract tesseract-lang ffmpeg
```

#### 2. Verification
```bash
which tesseract
# Apple Silicon: /opt/homebrew/bin/tesseract
# Intel: /usr/local/bin/tesseract
```
Zyntrix automatically checks both Homebrew prefixes.

---

### D. Docker & Container Deployment

Here is the production Dockerfile incorporating all multi-modal Layer 1 binaries:

```dockerfile
FROM python:3.11-slim-bullseye

# Install system binaries for PDF, OCR, and Audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Environment configuration
ENV ENVIRONMENT=production
ENV DEMO_MODE=false
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3. Runtime Diagnostics Contract

You can inspect the live operational state of all Layer 1 dependencies at any time:

```http
GET /api/v1/system/dependencies
```

### Response Status Definitions:
1. **`FUNCTIONAL`**: Technology is installed, configured, and a live execution test succeeded.
2. **`CONFIGURED`**: Executable or API key is found, ready for execution.
3. **`FALLBACK_ACTIVE`**: System binary is absent; offline deterministic/regex parser active.
4. **`NOT_CONFIGURED`**: External service key not provided.
5. **`FAILED`**: Technology encountered an execution error.
