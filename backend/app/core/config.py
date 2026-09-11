import os
from pathlib import Path
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory (device & OS independent)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "BIS Compliance Compiler"
    PROJECT_TEAM: str = "Zyntrix"
    SIH_PROBLEM_ID: str = "26107"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Server Host and Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Demo / Judge Mode
    DEMO_MODE: bool = False

    # Multi-Modal Layer 1 Services Configuration
    TESSERACT_CMD: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # M23 ML/DL Intelligence Layer Feature Flags
    ML_ENABLED: bool = True
    PRODUCT_EXTRACTION_ML_ENABLED: bool = True
    RERANKER_ENABLED: bool = True
    EVIDENCE_MATCHING_ML_ENABLED: bool = True
    ANOMALY_DETECTION_ENABLED: bool = True
    NLI_ENABLED: bool = True
    APPLICABILITY_CLASSIFIER_ENABLED: bool = False

    # M24 LangChain Reasoning Graph Feature Flags
    LANGCHAIN_LLM_ADAPTER_ENABLED: bool = False
    LANGGRAPH_ORCHESTRATOR_ENABLED: bool = False

    # LangSmith Observability Configuration (M24.5)
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "zyntrix-bis-compliance"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Security & CORS
    SECRET_KEY: str = "zyntrix-development-secret-key-change-in-production"
    ALLOWED_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Database Configuration (PostgreSQL + pgvector or SQLite dev fallback)
    DATABASE_URL: Optional[str] = None
    DEV_FALLBACK_SQLITE: bool = True
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgrespassword"
    POSTGRES_DB: str = "bis_compliance_db"
    
    # Storage & Upload limits (OS-independent Pathlib)
    STORAGE_LOCAL_PATH: str = str(BASE_DIR / "storage")
    UPLOADS_LOCAL_PATH: str = str(BASE_DIR / "uploads")
    LOGS_LOCAL_PATH: str = str(BASE_DIR / "logs")
    GENERATED_LOCAL_PATH: str = str(BASE_DIR / "generated")
    DATA_PATH: str = str(BASE_DIR / "data")
    
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain",
        "application/json",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        """Check if active database target is SQLite."""
        target = self.DATABASE_URL or ""
        return "sqlite" in target.lower()

    @property
    def async_database_url(self) -> str:
        """Asynchronous database connection URL."""
        if self.DATABASE_URL:
            raw = self.DATABASE_URL
            if raw.startswith("postgresql://"):
                return raw.replace("postgresql://", "postgresql+psycopg://", 1)
            elif raw.startswith("postgres://"):
                return raw.replace("postgres://", "postgresql+psycopg://", 1)
            elif raw.startswith("sqlite://"):
                return raw.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return raw

        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Synchronous database connection URL."""
        if self.DATABASE_URL:
            raw = self.DATABASE_URL
            if raw.startswith("postgresql+psycopg://"):
                return raw.replace("postgresql+psycopg://", "postgresql://", 1)
            elif raw.startswith("sqlite+aiosqlite://"):
                return raw.replace("sqlite+aiosqlite://", "sqlite://", 1)
            return raw

        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def ensure_directories(self) -> None:
        """Automatically create required runtime directories."""
        for path_str in [
            self.STORAGE_LOCAL_PATH,
            self.UPLOADS_LOCAL_PATH,
            self.LOGS_LOCAL_PATH,
            self.GENERATED_LOCAL_PATH,
            self.DATA_PATH,
        ]:
            try:
                p = Path(path_str)
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
settings.ensure_directories()
