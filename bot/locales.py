# bot/locales.py

TEXTS = {
    "ru": {
        "start_welcome": "👋 Привет! Я бот для приема заявок.\nНажми кнопку ниже, чтобы оставить заявку.",
        "btn_create_ticket": "📝 Оставить заявку",
        "fsm_name": "Шаг 1/3. Как вас зовут?",
        "fsm_phone": "Шаг 2/3. Укажите ваш телефон для связи (нажмите кнопку ниже или напишите вручную):",
        "btn_share_contact": "📱 Отправить мой номер",
        "fsm_description": "Шаг 3/3. Опишите вашу проблему или вопрос:",
        "ticket_created": "✅ Спасибо! Ваша заявка №{ticket_id} принята. Мы свяжемся с вами.",
        "btn_cancel": "❌ Отмена",
        "cancelled": "Действие отменено.",
        "manager_new_ticket": "🔔 <b>Новая заявка!</b>\n\n{ticket_card}",
        "my_tickets_empty": "У вас нет активных заявок.",
        "my_tickets_header": "📋 <b>Ваши активные заявки:</b>\n\n",
        "status_new": "🆕 Новая",
        "status_in_progress": "⏳ В работе",
        "status_done": "✅ Выполнена",
        "status_cancelled": "❌ Отменена",
        "notify_status_changed": "🔔 Статус вашей заявки №{ticket_id} изменен на: <b>{status}</b>.",
        "btn_rate": "Оценить работу от 1 до 5",
        "thanks_rating": "Спасибо за оценку {rating} из 5!",
        "stats_header": "📊 <b>Статистика заявок</b>",
        "stats_body": "Всего: {total}\n🆕 Новых: {new}\n⏳ В работе: {in_progress}\n✅ Выполнено: {done}\n❌ Отменено: {cancelled}\n⭐ Средний рейтинг: {avg_rating}",
        "privacy_warning": "⚠️ <i>Важно: чтобы менеджер мог написать вам в личные сообщения, убедитесь, что в настройках приватности Telegram у вас разрешено получение сообщений (или открыт доступ по ссылке).</i>",
    },
    "en": {
        "start_welcome": "👋 Hello! I am a ticket bot.\nPress the button below to create a ticket.",
        "btn_create_ticket": "📝 Create ticket",
        "fsm_name": "Step 1/3. What is your name?",
        "fsm_phone": "Step 2/3. Your phone number (click the button below or type manually):",
        "btn_share_contact": "📱 Share my phone",
        "fsm_description": "Step 3/3. Describe your issue:",
        "ticket_created": "✅ Thank you! Your ticket №{ticket_id} has been created.",
        "btn_cancel": "❌ Cancel",
        "cancelled": "Action cancelled.",
        "manager_new_ticket": "🔔 <b>New ticket!</b>\n\n{ticket_card}",
        "my_tickets_empty": "You have no active tickets.",
        "my_tickets_header": "📋 <b>Your active tickets:</b>\n\n",
        "status_new": "🆕 New",
        "status_in_progress": "⏳ In progress",
        "status_done": "✅ Done",
        "status_cancelled": "❌ Cancelled",
        "notify_status_changed": "🔔 Status of your ticket №{ticket_id} changed to: <b>{status}</b>.",
        "btn_rate": "Rate from 1 to 5",
        "thanks_rating": "Thanks for rating {rating} out of 5!",
        "stats_header": "📊 <b>Ticket Statistics</b>",
        "stats_body": "Total: {total}\n🆕 New: {new}\n⏳ In progress: {in_progress}\n✅ Done: {done}\n❌ Cancelled: {cancelled}\n⭐ Avg rating: {avg_rating}",
        "privacy_warning": "⚠️ <i>Important: so the manager can message you privately, please ensure your Telegram privacy settings allow receiving messages (or open link access).</i>",
    },
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Хелпер для получения текста с подстановкой переменных."""
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text
