from google_api.models import Ticket, TicketStatus
from bot.locales import get_text


def _translate_status(status: TicketStatus, lang: str) -> str:
    return get_text(f"status_{status.value}", lang=lang)


def format_ticket_card(ticket: Ticket, lang: str = "ru") -> str:
    status_str = _translate_status(ticket.status, lang)
    date_str = ticket.created_at.strftime("%d.%m.%Y %H:%M")
    
    if ticket.telegram_id:
        name_str = f'<a href="tg://user?id={ticket.telegram_id}">{ticket.name}</a>'
    else:
        name_str = ticket.name
        
    text = (
        f"<b>Заявка №{ticket.ticket_id}</b>\n\n"
        f"📅 {date_str}\n"
        f"👤 {name_str}\n"
        f"📞 {ticket.phone}\n\n"
        f"📝 {ticket.description}\n\n"
        f"📊 Статус: {status_str}"
    )
    
    if ticket.rating is not None:
        text += f"\n⭐ Оценка: {ticket.rating}/5"
        
    return text