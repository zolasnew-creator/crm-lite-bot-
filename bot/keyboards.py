from zoneinfo import ZoneInfo

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.locales import get_text
from config import settings
from google_api.models import Ticket, TicketStatus


def get_main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=get_text("btn_create_ticket", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=get_text("btn_cancel", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_phone_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=get_text("btn_share_contact", lang), request_contact=True))
    builder.row(KeyboardButton(text=get_text("btn_cancel", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_manager_status_kb(ticket_id: str, status: TicketStatus) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if status == TicketStatus.NEW:
        builder.row(
            InlineKeyboardButton(text="⏳ Принять", callback_data=f"status:{ticket_id}:in_progress")
        )

    builder.row(
        InlineKeyboardButton(text="✅ Закрыть", callback_data=f"status:{ticket_id}:done"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status:{ticket_id}:cancelled"),
    )
    return builder.as_markup()


def get_tickets_list_kb(tickets: list[Ticket], offset: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    local_tz = ZoneInfo(settings.timezone)

    for t in tickets:
        status_emoji = "🆕" if t.status == TicketStatus.NEW else "⏳"

        local_dt = t.created_at.astimezone(local_tz)
        time_str = local_dt.strftime("%H:%M")

        short_name = t.name[:15] + "..." if len(t.name) > 15 else t.name

        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} {time_str} | {t.ticket_id} | {short_name}",
                callback_data=f"view:{t.ticket_id}:{offset}",
            )
        )

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_page:{offset - 5}")
        )
    if offset + 5 < total:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_page:{offset + 5}")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def get_ticket_view_kb(ticket_id: str, status: TicketStatus, offset: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if status == TicketStatus.NEW:
        builder.row(
            InlineKeyboardButton(
                text="⏳ Принять", callback_data=f"status:{ticket_id}:in_progress:{offset}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="✅ Закрыть", callback_data=f"status:{ticket_id}:done:{offset}"),
        InlineKeyboardButton(
            text="❌ Отклонить", callback_data=f"status:{ticket_id}:cancelled:{offset}"
        ),
    )
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list_page:{offset}"))
    return builder.as_markup()


def get_rating_kb(ticket_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate:{ticket_id}:{i}"))

    builder.adjust(5)
    return builder.as_markup()
