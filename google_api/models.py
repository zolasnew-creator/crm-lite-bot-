from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class TicketStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticket_id: str
    created_at: datetime
    updated_at: datetime
    telegram_id: int | None = None
    name: str
    phone: str
    description: str
    status: TicketStatus
    rating: int | None = None
