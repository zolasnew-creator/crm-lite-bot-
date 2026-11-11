from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.locales import get_text
from google_api.models import TicketStatus


def get_main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=get_text("btn_create_ticket", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=get_text("btn_cancel", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_manager_status_kb(ticket_id: str, status: TicketStatus) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Принять" есть только у новых заявок
    if status == TicketStatus.NEW:
        builder.row(
            InlineKeyboardButton(text="⏳ Принять", callback_data=f"status:{ticket_id}:in_progress")
        )
        
    builder.row(
        InlineKeyboardButton(text="✅ Закрыть", callback_data=f"status:{ticket_id}:done"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status:{ticket_id}:cancelled"),
    )
    return builder.as_markup()


def get_rating_kb(ticket_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate:{ticket_id}:{i}"))
        
    builder.adjust(5)
    return builder.as_markup()