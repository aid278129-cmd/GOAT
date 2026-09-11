# Zyntrix BIS Compliance Compiler — Portable Deployment Guide

This guide provides exact, device-independent instructions for deploying and running the Zyntrix BIS Compliance Compiler across Windows, Linux, macOS, Docker containers, and offline Judge/Demo laptops.

---

## 1. System Requirements & Compatibility

| Component | Minimum Version | Recommended Version |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, Ubuntu 20.04+, macOS 12+ | Windows 11 / Ubuntu 22.04 LTS |
| **Python** | 3.10 | 3.12 or 3.14 |
| **Node.js** | 18.0.0 LTS | 20+ LTS |
| **Database (Optional)** | None (Auto-SQLite fallback) | PostgreSQL 16 with `pgvector` |

---

## 2. One-Command Quick Start

### A. Windows
Open Command Prompt or PowerShell in the repository root:
```bat
start.bat
```
To automatically install dependencies on first run:
```bat
start.bat --install
```

### B. Linux & macOS
Open Terminal in the repository root:
```bash
chmod +x start.sh
./start.sh
```
To automatically install dependencies on first run:
```bash
./start.sh --install
```

---

## 3. Docker Production Deployment

Run the complete multi-service stack (PostgreSQL 16 + pgvector, FastAPI Backend, React Frontend with Nginx reverse proxy):

```bash
# 1. Build images
docker compose build

# 2. Start all services in background
docker compose up -d

# 3. View live health status
docker compose ps
```

### Access URLs:
- **Frontend Web UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API Gateway**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Diagnostics**: [http://localhost:8000/api/v1/system/health](http://localhost:8000/api/v1/system/health)

---

## 4. Judge / Demo Offline Laptop Mode

The Zyntrix architecture includes an automatic, zero-dependency offline mode designed specifically for hackathon evaluation and conference demonstrations where PostgreSQL is not installed:

1. **Zero External DB Requirement**:
   - If PostgreSQL is not reachable, Zyntrix automatically connects to a local embedded SQLite database at `data/zyntrix.db`.
   - Vector similarity automatically runs in-process using high-performance Python dense cosine embeddings.
2. **Instant Pre-Seeded Assessment**:
   - The verified SIH golden demonstration assessment is pre-seeded in memory on startup.
3. **Run Command**:
   ```bash
   # Windows
   start.bat
   
   # Linux / macOS
   ./start.sh
   ```
   No database configuration, cloud API keys, or internet connection required.

---

## 5. Environment Variables Reference

Copy `.env.example` to `.env` to customize settings:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | Network binding interface |
| `PORT` | `8000` | Backend API port |
| `DATABASE_URL` | None | Direct database URL (`postgresql+psycopg://...` or `sqlite+aiosqlite://...`) |
| `DEV_FALLBACK_SQLITE` | `True` | Automatically use local SQLite if PostgreSQL is unreachable |
| `ALLOWED_CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated or JSON list) |
| `DEMO_MODE` | `False` | Mark system in demonstration mode |
| `VITE_API_BASE_URL` | `""` (proxy) | Frontend API endpoint (override for hosted deployments) |

---

## 6. Verification and Health Checks

Check operational subsystem health at any time:
```bash
curl http://localhost:8000/api/v1/system/health
```

Expected response:
```json
{
  "status": "ok",
  "api": "ok",
  "database": {
    "status": "ok",
    "type": "postgresql",
    "connected": true
  },
  "pgvector": {
    "status": "ok",
    "mode": "pgvector_extension"
  },
  "knowledge_base": {
    "status": "ok",
    "verified_standards_count": 4,
    "provenance": "OFFICIAL_BIS_QCO_CATALOG"
  },
  "configuration": {
    "environment": "development",
    "demo_mode": false,
    "host": "0.0.0.0",
    "port": 8000
  }
}
```
