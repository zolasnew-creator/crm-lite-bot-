from google_api.models import TicketStatus
from google_api.sheets import _row_to_ticket


def test_row_to_ticket_parses_data_correctly():
    """Проверяем парсинг строки из таблицы (включая числа вместо строк)."""
    row = {
        "ticket_id": "T-ABC",
        "created_at": "2026-11-11T12:00:00+00:00",
        "updated_at": "2026-11-11T12:05:00+00:00",
        "telegram_id": 123456,  # Google может вернуть число
        "name": "Ivan",
        "phone": 79991234567,  # А тут вернул int!
        "description": "Help",
        "status": "new",
        "rating": "",  # Пустая строка, должна стать None
    }

    ticket = _row_to_ticket(row)

    assert ticket.ticket_id == "T-ABC"
    assert ticket.phone == "79991234567"  # Убедились, что привелось к строке
    assert ticket.telegram_id == 123456
    assert ticket.status == TicketStatus.NEW
    assert ticket.rating is None
