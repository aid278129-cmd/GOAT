import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.app.database.session import engine
from backend.app.models.base import Base
import backend.app.models

async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("ALL_TABLES_CREATED_OK")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
