import aiosqlite
from loguru import logger

from config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    telegram_id INTEGER,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    rating INTEGER
);

CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
        logger.info(f"Database initialized at {settings.db_path}")


async def get_db_connection() -> aiosqlite.Connection:
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    return db