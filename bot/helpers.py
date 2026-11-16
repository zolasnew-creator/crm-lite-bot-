from aiogram.types import Message


def get_user_lang(message: Message) -> str:
    """Определяет язык пользователя (пока поддерживаем только ru и en)."""
    return "ru" if message.from_user.language_code == "ru" else "en"
