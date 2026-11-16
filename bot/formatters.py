from zoneinfo import ZoneInfo

from bot.locales import get_text
from config import settings
from google_api.models import Ticket, TicketStatus


def _translate_status(status: TicketStatus, lang: str) -> str:
    return get_text(f"status_{status.value}", lang=lang)


def format_ticket_card(ticket: Ticket, lang: str = "ru") -> str:
    status_str = _translate_status(ticket.status, lang)

    local_tz = ZoneInfo(settings.timezone)
    local_dt = ticket.created_at.astimezone(local_tz)
    date_str = local_dt.strftime("%d.%m.%Y %H:%M")

    if ticket.telegram_id:
        name_str = f'<a href="tg://user?id={ticket.telegram_id}">{ticket.name}</a>'
    else:
        name_str = ticket.name

    text = (
        f"<b>Заявка №{ticket.ticket_id}</b>\n"
        f"📅 {date_str}\n"
        f"👤 {name_str}\n"
        f"📞 {ticket.phone}\n"
        f"📝 {ticket.description}\n"
        f"📊 Статус: {status_str}"
    )

    if ticket.rating is not None:
        text += f"\n⭐ Оценка: {ticket.rating}/5"

    return text
