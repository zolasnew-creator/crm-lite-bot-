from datetime import datetime
import aiosqlite

from google_api.models import Ticket, TicketStatus


class TicketRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def upsert(self, ticket: Ticket) -> None:
        await self.db.execute(
            """
            INSERT INTO tickets (
                ticket_id, created_at, updated_at, telegram_id, name, phone, description, status, rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticket_id) DO UPDATE SET
                updated_at=excluded.updated_at,
                telegram_id=excluded.telegram_id,
                name=excluded.name,
                phone=excluded.phone,
                description=excluded.description,
                status=excluded.status,
                rating=excluded.rating
            """,
            (
                ticket.ticket_id,
                ticket.created_at.isoformat(),
                ticket.updated_at.isoformat(),
                ticket.telegram_id,
                ticket.name,
                ticket.phone,
                ticket.description,
                ticket.status.value,
                ticket.rating,
            ),
        )
        await self.db.commit()

    async def get_by_id(self, ticket_id: str) -> Ticket | None:
        async with self.db.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_ticket(row) if row else None

    async def get_active(self) -> list[Ticket]:
        async with self.db.execute(
            "SELECT * FROM tickets WHERE status IN (?, ?) ORDER BY updated_at DESC",
            (TicketStatus.NEW.value, TicketStatus.IN_PROGRESS.value),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_ticket(r) for r in rows]

    async def get_updated_since(self, ts: datetime) -> list[Ticket]:
        async with self.db.execute(
            "SELECT * FROM tickets WHERE updated_at > ? ORDER BY updated_at ASC",
            (ts.isoformat(),),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_ticket(r) for r in rows]

    async def get_stats(self) -> dict:
        async with self.db.execute("SELECT COUNT(*) FROM tickets") as cursor:
            total = (await cursor.fetchone())[0]

        async with self.db.execute(
            "SELECT status, COUNT(*) as count, AVG(rating) as avg_rating FROM tickets GROUP BY status"
        ) as cursor:
            rows = await cursor.fetchall()
        
        stats = {
            "total": total,
            "new": 0, 
            "in_progress": 0, 
            "done": 0, 
            "cancelled": 0, 
            "avg_rating": 0.0
        }
        total_rated = 0
        sum_ratings = 0.0

        for row in rows:
            stats[row["status"]] = row["count"]
            if row["status"] == "done" and row["avg_rating"]:
                total_rated += row["count"]
                sum_ratings += row["avg_rating"] * row["count"]

        if total_rated > 0:
            stats["avg_rating"] = round(sum_ratings / total_rated, 2)

        return stats

    async def set_sync_ts(self, ts: datetime) -> None:
        await self.db.execute(
            "INSERT INTO sync_state (key, value) VALUES ('last_sync_ts', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (ts.isoformat(),),
        )
        await self.db.commit()

    async def get_sync_ts(self) -> datetime | None:
        async with self.db.execute(
            "SELECT value FROM sync_state WHERE key = 'last_sync_ts'"
        ) as cursor:
            row = await cursor.fetchone()
            return datetime.fromisoformat(row["value"]) if row else None

    def _row_to_ticket(self, row: aiosqlite.Row) -> Ticket:
        return Ticket(
            ticket_id=row["ticket_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            telegram_id=row["telegram_id"],
            name=row["name"],
            phone=row["phone"],
            description=row["description"],
            status=TicketStatus(row["status"]),
            rating=row["rating"],
        )