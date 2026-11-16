from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.formatters import format_ticket_card
from bot.helpers import get_user_lang
from bot.keyboards import (
    get_cancel_kb,
    get_main_menu_kb,
    get_manager_status_kb,
    get_phone_kb,
)
from bot.locales import get_text
from config import settings
from services.ticket_service import TicketService


class TicketForm(StatesGroup):
    name = State()
    phone = State()
    description = State()


def build_client_router(service: TicketService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        lang = get_user_lang(message)
        await message.answer(get_text("start_welcome", lang), reply_markup=get_main_menu_kb(lang))

    @router.message(F.text.in_({"📝 Оставить заявку", "📝 Create ticket"}))
    async def start_ticket_fsm(message: Message, state: FSMContext):
        lang = get_user_lang(message)
        await state.set_state(TicketForm.name)

        await message.answer(get_text("privacy_warning", lang))
        await message.answer(get_text("fsm_name", lang), reply_markup=get_cancel_kb(lang))

    @router.message(Command("cancel"))
    @router.message(F.text.in_({"❌ Отмена", "❌ Cancel"}))
    async def cancel_handler(message: Message, state: FSMContext):
        lang = get_user_lang(message)
        await state.clear()
        await message.answer(get_text("cancelled", lang), reply_markup=get_main_menu_kb(lang))

    # Добавили F.text, чтобы бот не падал, если прислать стикер
    @router.message(TicketForm.name, F.text)
    async def process_name(message: Message, state: FSMContext):
        lang = get_user_lang(message)
        await state.update_data(name=message.text)
        await state.set_state(TicketForm.phone)
        await message.answer(get_text("fsm_phone", lang), reply_markup=get_phone_kb(lang))

    @router.message(TicketForm.phone)
    async def process_phone(message: Message, state: FSMContext):
        lang = get_user_lang(message)

        phone = message.contact.phone_number if message.contact else message.text

        await state.update_data(phone=phone)
        await state.set_state(TicketForm.description)
        await message.answer(get_text("fsm_description", lang), reply_markup=get_cancel_kb(lang))

    @router.message(TicketForm.description, F.text)
    async def process_description(message: Message, state: FSMContext):
        lang = get_user_lang(message)
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
            reply_markup=get_manager_status_kb(ticket.ticket_id, ticket.status),
        )

    @router.message(Command("my_tickets"))
    async def cmd_my_tickets(message: Message):
        lang = get_user_lang(message)
        # Используем оптимизированный запрос к БД
        user_tickets = await service.repo.get_by_telegram_id(message.from_user.id)

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

        ticket = await service.repo.get_by_id(ticket_id)

        # ИСПРАВЛЕНИЕ IDOR: проверяем, что заявка принадлежит тому, кто нажал
        if not ticket or ticket.telegram_id != callback.from_user.id:
            await callback.answer("Заявка не найдена", show_alert=True)
            return

        # Защита от повторной оценки
        if ticket.rating is not None:
            await callback.answer("Вы уже оценили эту заявку", show_alert=True)
            return

        updated_ticket = await service.rate_ticket(ticket_id, rating)

        if updated_ticket:
            await callback.message.edit_text(get_text("thanks_rating", "ru", rating=rating))
        else:
            await callback.answer("Ошибка при сохранении оценки", show_alert=True)
        await callback.answer()

    return router
