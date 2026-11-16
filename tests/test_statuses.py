from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from google_api.models import Ticket, TicketStatus
from services.ticket_service import TicketService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return TicketService(mock_repo)


@pytest.mark.asyncio
async def test_illegal_transition_new_to_done(service, mock_repo):
    """Проверяем, что нельзя перевести заявку из NEW сразу в DONE."""
    ticket = Ticket(
        ticket_id="T-123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        telegram_id=1,
        name="Test",
        phone="123",
        description="Test",
        status=TicketStatus.NEW,
    )
    mock_repo.get_by_id.return_value = ticket

    with patch("services.ticket_service.sheets", new_callable=AsyncMock) as mock_sheets:
        result = await service.change_status("T-123", TicketStatus.DONE)

        assert result is None
        mock_sheets.update_ticket.assert_not_called()
        mock_repo.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_valid_transition_new_to_in_progress(service, mock_repo):
    """Проверяем, что переход из NEW в IN_PROGRESS работает."""
    ticket = Ticket(
        ticket_id="T-123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        telegram_id=1,
        name="Test",
        phone="123",
        description="Test",
        status=TicketStatus.NEW,
    )
    mock_repo.get_by_id.return_value = ticket

    with patch("services.ticket_service.sheets", new_callable=AsyncMock) as mock_sheets:
        result = await service.change_status("T-123", TicketStatus.IN_PROGRESS)

        assert result is not None
        assert result.status == TicketStatus.IN_PROGRESS
        mock_sheets.update_ticket.assert_called_once()
        mock_repo.upsert.assert_called_once()
