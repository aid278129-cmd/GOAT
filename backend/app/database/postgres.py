from sqlalchemy import text
from backend.app.database.session import engine
from backend.app.core.logging import logger


async def init_db_extensions() -> None:
    """Initialize essential PostgreSQL extensions if available."""
    for ext in ['"uuid-ossp"', "vector"]:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext};"))
                logger.info(f"PostgreSQL extension '{ext}' initialized successfully.")
        except Exception as exc:
            logger.info(f"PostgreSQL extension '{ext}' not installed or skipped: {exc}")
