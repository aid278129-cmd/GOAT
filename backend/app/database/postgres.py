from sqlalchemy import text
from backend.app.database.session import engine
from backend.app.core.logging import logger


async def init_db_extensions() -> None:
    """Initialize essential PostgreSQL extensions including pgvector and uuid-ossp."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            logger.info("PostgreSQL extensions initialized successfully (vector, uuid-ossp).")
    except Exception as exc:
        logger.warning(f"Could not initialize PostgreSQL extensions automatically: {exc}")
