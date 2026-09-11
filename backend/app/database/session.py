import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.base import Base


def create_resilient_engine(url: str):
    """Create SQLAlchemy async engine with driver-specific configuration."""
    if "sqlite" in url:
        return create_async_engine(
            url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# Active engine and session factory
engine = create_resilient_engine(settings.async_database_url)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

_DB_AVAILABLE: bool = False


async def test_db_connectivity(retries: int = 1, delay_sec: float = 0.2) -> bool:
    """Test database responsiveness with bounded retries and automatic local fallback."""
    global _DB_AVAILABLE, engine, AsyncSessionLocal
    for attempt in range(retries + 1):
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    _DB_AVAILABLE = True
                    return True
        except Exception:
            if attempt < retries:
                await asyncio.sleep(delay_sec)

    # Automatic local database fallback for development and offline demo
    if settings.DEV_FALLBACK_SQLITE and not settings.is_sqlite and settings.ENVIRONMENT != "production":
        sqlite_db_path = f"{settings.DATA_PATH}/zyntrix.db"
        sqlite_url = f"sqlite+aiosqlite:///{sqlite_db_path}"
        try:
            fallback_engine = create_resilient_engine(sqlite_url)
            async with fallback_engine.connect() as conn:
                res = await conn.execute(text("SELECT 1"))
                if res.scalar() == 1:
                    engine = fallback_engine
                    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
                    _DB_AVAILABLE = True
                    logger.info(f"Connected to local portable SQLite database at {sqlite_db_path}")
                    return True
        except Exception as fb_exc:
            logger.debug(f"SQLite fallback check: {fb_exc}")

    _DB_AVAILABLE = False
    return False


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency for obtaining async database session with resilient standalone fallback."""
    if not _DB_AVAILABLE:
        yield None
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> dict:
    """Verify raw database connectivity or report standalone readiness."""
    global _DB_AVAILABLE
    if await test_db_connectivity(retries=1):
        is_sq = "sqlite" in str(engine.url)
        db_type = "sqlite" if is_sq else "postgresql"
        return {
            "status": "ok",
            "database_type": db_type,
            "connected": True,
            "message": f"{db_type.capitalize()} database connection active and responsive",
        }
    return {
        "status": "standalone_ready",
        "database_type": "in_memory",
        "connected": False,
        "mode": "in_memory_standalone",
        "message": "Zero external dependencies: in-memory state active.",
    }


async def check_pgvector_extension() -> dict:
    """Verify whether pgvector extension is installed or in-memory vector retrieval is active."""
    if not _DB_AVAILABLE or "sqlite" in str(engine.url):
        return {
            "status": "standalone_ready",
            "mode": "dense_cosine_python",
            "message": "In-memory dense cosine vector similarity active (standalone fallback).",
        }
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()
            if row:
                return {
                    "status": "ok",
                    "extension": row[0],
                    "version": row[1],
                    "message": "pgvector extension active",
                }
    except Exception as exc:
        logger.warning(f"pgvector check notice: {exc}")
    return {
        "status": "standalone_ready",
        "mode": "dense_cosine_python",
        "message": "In-memory dense cosine vector similarity active (standalone fallback).",
    }


async def create_tables_if_needed() -> None:
    """Create database tables if connected to database schema."""
    if not _DB_AVAILABLE:
        await test_db_connectivity(retries=1)
    if _DB_AVAILABLE:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info(f"Database schema verified/created successfully on {engine.url.drivername}.")
        except Exception as exc:
            logger.warning(f"Database table creation notice: {exc}")
