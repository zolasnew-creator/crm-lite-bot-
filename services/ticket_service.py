import uuid
from datetime import UTC, datetime

from loguru import logger

from google_api import sheets
from google_api.models import Ticket, TicketStatus
from storage.repository import TicketRepository

# Легальные переходы: из какого статуса в какие можно перейти
ALLOWED_TRANSITIONS = {
    TicketStatus.NEW: {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED},
    TicketStatus.IN_PROGRESS: {TicketStatus.DONE, TicketStatus.CANCELLED},
    TicketStatus.DONE: set(),
    TicketStatus.CANCELLED: set(),
}


class TicketService:
    def __init__(self, repo: TicketRepository):
        self.repo = repo

    async def create_ticket(
        self, telegram_id: int, name: str, phone: str, description: str
    ) -> Ticket:
        now = datetime.now(UTC)
        ticket = Ticket(
            ticket_id=f"T-{uuid.uuid4().hex[:6].upper()}",
            created_at=now,
            updated_at=now,
            telegram_id=telegram_id,
            name=name,
            phone=phone,
            description=description,
            status=TicketStatus.NEW,
            rating=None,
        )

        # Сначала пишем в SQLite (источник правды, не теряем данные)
        await self.repo.upsert(ticket)

        # Затем пытаемся синхронизировать с Google Sheets
        try:
            await sheets.append_ticket(ticket)
        except Exception as e:
            logger.error(f"Failed to sync new ticket {ticket.ticket_id} to Sheets: {e}")
            # TODO: Добавить механизм досылки в Google Sheets при восстановлении связи

        logger.info(f"Created ticket {ticket.ticket_id} for user {telegram_id}")
        return ticket

    async def change_status(self, ticket_id: str, new_status: TicketStatus) -> Ticket | None:
        ticket = await self.repo.get_by_id(ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found for status change")
            return None

        if new_status not in ALLOWED_TRANSITIONS[ticket.status]:
            logger.warning(f"Illegal transition {ticket.status} -> {new_status}")
            return None

        updated_ticket = ticket.model_copy(
            update={
                "status": new_status,
                "updated_at": datetime.now(UTC),
            }
        )

        await self.repo.upsert(updated_ticket)

        try:
            await sheets.update_ticket(updated_ticket)
        except Exception as e:
            logger.error(f"Failed to update ticket {ticket_id} in Sheets: {e}")

        return updated_ticket

    async def rate_ticket(self, ticket_id: str, rating: int) -> Ticket | None:
        ticket = await self.repo.get_by_id(ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found for rating")
            return None

        updated_ticket = ticket.model_copy(
            update={
                "rating": rating,
                "updated_at": datetime.now(UTC),
            }
        )

        await self.repo.upsert(updated_ticket)

        try:
            await sheets.update_ticket(updated_ticket)
        except Exception as e:
            logger.error(f"Failed to update rating for ticket {ticket_id} in Sheets: {e}")

        logger.info(f"Ticket {ticket_id} rated {rating}")
        return updated_ticket

    async def sync_from_sheets(self) -> None:
        """Полный pull из Sheets в SQLite (при старте)."""
        logger.info("Starting full sync from Google Sheets...")
        all_tickets = await sheets.get_all_tickets()
        for t in all_tickets:
            await self.repo.upsert(t)

        await self.repo.set_sync_ts(datetime.now(UTC))
        logger.info(f"Full sync complete. Synced {len(all_tickets)} tickets.")

    async def sync_delta(self) -> list[Ticket]:
        """Инкрементальный pull (раз в 3 минуты)."""
        last_ts = await self.repo.get_sync_ts()
        if not last_ts:
            await self.sync_from_sheets()
            return []

        delta_tickets = await sheets.get_tickets_updated_since(last_ts)
        if not delta_tickets:
            return []

        for t in delta_tickets:
            await self.repo.upsert(t)

        now = datetime.now(UTC)
        await self.repo.set_sync_ts(now)
        logger.info(f"Delta sync complete. Updated {len(delta_tickets)} tickets.")
        return delta_tickets
