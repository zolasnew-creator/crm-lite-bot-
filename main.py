import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from loguru import logger

from bot.handlers.client import build_client_router
from bot.handlers.manager import build_manager_router
from bot.keyboards import get_rating_kb
from bot.locales import get_text
from config import settings
from google_api.models import TicketStatus
from services.ticket_service import TicketService
from storage.db import get_db_connection, init_db
from storage.repository import TicketRepository


async def sync_task(bot: Bot, service: TicketService):
    """Фоновая задача для периодического pull'а изменений из Google Sheets."""
    while True:
        try:
            await asyncio.sleep(settings.sync_interval_seconds)
            logger.info("Running periodic delta sync...")

            delta_tickets = await service.sync_delta()

            for ticket in delta_tickets:
                if ticket.telegram_id:
                    status_text = get_text(f"status_{ticket.status.value}", "ru")
                    notify_text = get_text(
                        "notify_status_changed",
                        "ru",
                        ticket_id=ticket.ticket_id,
                        status=status_text,
                    )

                    reply_markup = None
                    if ticket.status == TicketStatus.DONE and ticket.rating is None:
                        notify_text += "\n\n" + get_text("btn_rate", "ru")
                        reply_markup = get_rating_kb(ticket.ticket_id)

                    await bot.send_message(
                        ticket.telegram_id, notify_text, reply_markup=reply_markup
                    )
        except asyncio.CancelledError:
            logger.info("Sync task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background sync task: {e}")


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("Starting CRM Lite Bot...")

    await init_db()
    db_conn = await get_db_connection()
    repo = TicketRepository(db_conn)
    service = TicketService(repo)

    try:
        await service.sync_from_sheets()
    except Exception as e:
        logger.error(f"Failed to sync from sheets on startup: {e}")

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Устанавливаем меню команд (синяя кнопка слева от ввода)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="my_tickets", description="Мои активные заявки"),
            BotCommand(command="manager", description="Панель менеджера"),
            BotCommand(command="list", description="Список заявок (для менеджера)"),
            BotCommand(command="stats", description="Статистика (для менеджера)"),
        ]
    )

    dp = Dispatcher()
    dp.include_router(build_client_router(service))
    dp.include_router(build_manager_router(service))

    sync_task_handle = asyncio.create_task(sync_task(bot, service))

    logger.info("Bot is starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        sync_task_handle.cancel()
        await bot.session.close()
        await db_conn.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution stopped manually.")
