from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.filters import IsManager
from bot.formatters import format_ticket_card
from bot.keyboards import (
    get_rating_kb,
    get_ticket_view_kb,
    get_tickets_list_kb,
)
from bot.locales import get_text
from google_api.models import TicketStatus
from services.ticket_service import TicketService


def build_manager_router(service: TicketService) -> Router:
    router = Router()

    router.message.filter(IsManager())
    router.callback_query.filter(IsManager())

    @router.message(Command("manager"))
    async def cmd_manager(message: Message):
        await message.answer(
            "👨‍💼 Панель менеджера.\n"
            "Команда /list — показать активные заявки.\n"
            "Команда /stats — статистика по заявкам."
        )

    @router.message(Command("stats"))
    async def cmd_stats(message: Message):
        stats = await service.repo.get_stats()
        text = (
            get_text("stats_header", "ru")
            + "\n\n"
            + get_text(
                "stats_body",
                "ru",
                total=stats["total"],
                new=stats["new"],
                in_progress=stats["in_progress"],
                done=stats["done"],
                cancelled=stats["cancelled"],
                avg_rating=stats["avg_rating"],
            )
        )
        await message.answer(text)

    async def show_list(message: Message, offset: int, edit: bool = False):
        limit = 5
        tickets, total = await service.repo.get_active_paginated(limit, offset)

        if not tickets:
            text = "Нет активных заявок."
            kb = None
        else:
            page = offset // limit + 1
            total_pages = (total + limit - 1) // limit
            text = f"📋 <b>Активные заявки (Страница {page} из {total_pages})</b>\nВыберите заявку для управления:"
            kb = get_tickets_list_kb(tickets, offset, total)

        if edit:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)

    @router.message(Command("list"))
    async def cmd_list(message: Message):
        await show_list(message, offset=0)

    @router.callback_query(F.data.startswith("list_page:"))
    async def process_list_page(callback: CallbackQuery):
        offset = int(callback.data.split(":")[1])
        await show_list(callback.message, offset, edit=True)
        await callback.answer()

    @router.callback_query(F.data.startswith("view:"))
    async def process_view_ticket(callback: CallbackQuery):
        _, ticket_id, offset_str = callback.data.split(":")
        offset = int(offset_str)

        ticket = await service.repo.get_by_id(ticket_id)
        if not ticket:
            await callback.answer("Заявка не найдена", show_alert=True)
            return

        card = format_ticket_card(ticket, lang="ru")
        kb = get_ticket_view_kb(ticket.ticket_id, ticket.status, offset)

        await callback.message.edit_text(card, reply_markup=kb)
        await callback.answer()

    @router.callback_query(F.data.startswith("status:"))
    async def process_status_change(callback: CallbackQuery):
        parts = callback.data.split(":")
        ticket_id = parts[1]
        new_status_str = parts[2]
        offset = int(parts[3]) if len(parts) > 3 else 0

        try:
            new_status = TicketStatus(new_status_str)
        except ValueError:
            await callback.answer("Неизвестный статус")
            return

        updated_ticket = await service.change_status(ticket_id, new_status)

        if not updated_ticket:
            await callback.answer(
                "Ошибка: невозможно изменить статус (заявка не найдена или недопустимый переход)",
                show_alert=True,
            )
            return

        card = format_ticket_card(updated_ticket, lang="ru")

        if updated_ticket.status in (TicketStatus.DONE, TicketStatus.CANCELLED):
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list_page:{offset}")
            )
            keyboard = builder.as_markup()
        else:
            keyboard = get_ticket_view_kb(updated_ticket.ticket_id, updated_ticket.status, offset)

        await callback.message.edit_text(card, reply_markup=keyboard)
        await callback.answer("Статус обновлен")

        if updated_ticket.telegram_id:
            try:
                status_text = get_text(f"status_{updated_ticket.status.value}", "ru")
                notify_text = get_text(
                    "notify_status_changed",
                    "ru",
                    ticket_id=ticket_id,
                    status=status_text,
                )

                reply_markup = None
                if updated_ticket.status == TicketStatus.DONE:
                    notify_text += "\n\n" + get_text("btn_rate", "ru")
                    reply_markup = get_rating_kb(ticket_id)

                await callback.bot.send_message(
                    updated_ticket.telegram_id,
                    notify_text,
                    reply_markup=reply_markup,
                )
            except Exception as e:
                logger.error(f"Failed to notify client {updated_ticket.telegram_id}: {e}")

    return router
