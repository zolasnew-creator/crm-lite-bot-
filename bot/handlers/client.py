from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.formatters import format_ticket_card
from bot.keyboards import get_cancel_kb, get_main_menu_kb, get_rating_kb
from bot.locales import get_text
from config import settings
from google_api.models import TicketStatus
from services.ticket_service import TicketService


class TicketForm(StatesGroup):
    name = State()
    phone = State()
    description = State()


def build_client_router(service: TicketService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        await message.answer(
            get_text("start_welcome", lang), reply_markup=get_main_menu_kb(lang)
        )

    @router.message(F.text.in_({"📝 Оставить заявку", "📝 Create ticket"}))
    async def start_ticket_fsm(message: Message, state: FSMContext):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        await state.set_state(TicketForm.name)
        
        # Отправляем предупреждение о приватности и сразу задаем первый вопрос
        await message.answer(
            get_text("privacy_warning", lang)
        )
        await message.answer(
            get_text("fsm_name", lang), reply_markup=get_cancel_kb(lang)
        )

    @router.message(Command("cancel"))
    @router.message(F.text.in_({"❌ Отмена", "❌ Cancel"}))
    async def cancel_handler(message: Message, state: FSMContext):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        await state.clear()
        await message.answer(
            get_text("cancelled", lang), reply_markup=get_main_menu_kb(lang)
        )

    @router.message(TicketForm.name)
    async def process_name(message: Message, state: FSMContext):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        await state.update_data(name=message.text)
        await state.set_state(TicketForm.phone)
        await message.answer(get_text("fsm_phone", lang))

    @router.message(TicketForm.phone)
    async def process_phone(message: Message, state: FSMContext):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        await state.update_data(phone=message.text)
        await state.set_state(TicketForm.description)
        await message.answer(get_text("fsm_description", lang))

    @router.message(TicketForm.description)
    async def process_description(message: Message, state: FSMContext):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        data = await state.get_data()
        await state.clear()

        ticket = await service.create_ticket(
            telegram_id=message.from_user.id,
            name=data["name"],
            phone=data["phone"],
            description=message.text,
        )

        await message.answer(
            get_text("ticket_created", lang, ticket_id=ticket.ticket_id),
            reply_markup=get_main_menu_kb(lang),
        )

        card = format_ticket_card(ticket, lang="ru")
        await message.bot.send_message(
            settings.manager_id,
            get_text("manager_new_ticket", "ru", ticket_card=card),
        )

    @router.message(Command("my_tickets"))
    async def cmd_my_tickets(message: Message):
        lang = "ru" if message.from_user.language_code == "ru" else "en"
        active_tickets = await service.repo.get_active()
        user_tickets = [t for t in active_tickets if t.telegram_id == message.from_user.id]
        
        if not user_tickets:
            await message.answer(get_text("my_tickets_empty", lang))
            return

        header = get_text("my_tickets_header", lang)
        cards = "\n\n".join(format_ticket_card(t, lang) for t in user_tickets[:10])
        await message.answer(header + cards)

    @router.callback_query(F.data.startswith("rate:"))
    async def process_rating(callback: CallbackQuery):
        _, ticket_id, rating_str = callback.data.split(":")
        rating = int(rating_str)
        
        updated_ticket = await service.rate_ticket(ticket_id, rating)
        
        if updated_ticket:
            await callback.message.edit_text(
                get_text("thanks_rating", "ru", rating=rating)
            )
        else:
            await callback.answer("Заявка не найдена", show_alert=True)
        await callback.answer()

    return router