from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.filters import IsManager
from bot.formatters import format_ticket_card
from bot.keyboards import get_manager_status_kb, get_rating_kb
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
        text = get_text("stats_header", "ru") + "\n\n" + get_text(
            "stats_body", "ru",
            total=stats["total"],
            new=stats["new"],
            in_progress=stats["in_progress"],
            done=stats["done"],
            cancelled=stats["cancelled"],
            avg_rating=stats["avg_rating"],
        )
        await message.answer(text)

    @router.message(Command("list"))
    async def cmd_list(message: Message):
        active_tickets = await service.repo.get_active()

        if not active_tickets:
            await message.answer("Нет активных заявок.")
            return

        for t in active_tickets:
            card = format_ticket_card(t, lang="ru")
            await message.answer(
                card,
                reply_markup=get_manager_status_kb(t.ticket_id, t.status)
            )

    @router.callback_query(F.data.startswith("status:"))
    async def process_status_change(callback: CallbackQuery):
        _, ticket_id, new_status_str = callback.data.split(":")
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
            keyboard = None
        else:
            keyboard = get_manager_status_kb(updated_ticket.ticket_id, updated_ticket.status)

        await callback.message.edit_text(card, reply_markup=keyboard)
        await callback.answer("Статус обновлен")

        if updated_ticket.telegram_id:
            try:
                status_text = get_text(f"status_{updated_ticket.status.value}", "ru")
                notify_text = get_text(
                    "notify_status_changed", "ru",
                    ticket_id=ticket_id, status=status_text,
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