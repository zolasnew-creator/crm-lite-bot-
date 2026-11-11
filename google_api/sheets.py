import asyncio
from datetime import datetime

import gspread
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from google_api.auth import get_gspread_client
from google_api.models import Ticket, TicketStatus

# Оборачиваем вызовы к Google API в ретраи на случай 500/502/503/429
RETRY_EXCEPTIONS = (gspread.exceptions.APIError, TimeoutError)


async def _get_worksheet() -> gspread.Worksheet:
    client = await asyncio.to_thread(get_gspread_client)
    sheet = await asyncio.to_thread(client.open_by_key, settings.sheet_id)
    return await asyncio.to_thread(sheet.worksheet, settings.sheet_name)


def _ticket_to_row(ticket: Ticket) -> list[str | int | None]:
    return [
        ticket.ticket_id,
        ticket.created_at.isoformat(),
        ticket.updated_at.isoformat(),
        ticket.telegram_id,
        ticket.name,
        ticket.phone,
        ticket.description,
        ticket.status.value,
        ticket.rating,
    ]


def _row_to_ticket(row: dict) -> Ticket:
    # gspread возвращает пустые ячейки как пустые строки "",
    # а нам нужны None для int/None полей.
    tg_id = int(row["telegram_id"]) if row.get("telegram_id") else None
    rating = int(row["rating"]) if row.get("rating") else None
    
    return Ticket(
        ticket_id=str(row["ticket_id"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
        telegram_id=tg_id,
        name=str(row["name"]),
        phone=str(row["phone"]),
        description=str(row["description"]),
        status=TicketStatus(str(row["status"])),
        rating=rating,
    )


@retry(
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def append_ticket(ticket: Ticket) -> None:
    worksheet = await _get_worksheet()
    row = _ticket_to_row(ticket)
    await asyncio.to_thread(worksheet.append_row, row)
    logger.info(f"Appended ticket {ticket.ticket_id} to Sheets")


@retry(
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def update_ticket(ticket: Ticket) -> None:
    worksheet = await _get_worksheet()
    cell = await asyncio.to_thread(worksheet.find, ticket.ticket_id)
    if not cell:
        logger.error(f"Ticket {ticket.ticket_id} not found in Sheets for update")
        return

    row = _ticket_to_row(ticket)
    # Обновляем всю строку целиком (от колонки A до I)
    await asyncio.to_thread(
        worksheet.update,
        f"A{cell.row}:I{cell.row}",
        [row],
    )
    logger.info(f"Updated ticket {ticket.ticket_id} in Sheets")


@retry(
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def get_all_tickets() -> list[Ticket]:
    worksheet = await _get_worksheet()
    records = await asyncio.to_thread(worksheet.get_all_records)
    return [_row_to_ticket(r) for r in records]


@retry(
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def get_tickets_updated_since(ts: datetime) -> list[Ticket]:
    # Получаем всё и фильтруем локально. Для нашего объема данных (сотни строк) это быстрее,
    # чем дергать Google API фильтрами по каждой строке.
    all_tickets = await get_all_tickets()
    return [t for t in all_tickets if t.updated_at > ts]