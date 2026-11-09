import asyncio
from datetime import datetime, timezone
import uuid

from loguru import logger

from config import settings
from google_api.auth import get_gspread_client


async def main() -> None:
    logger.info("Connecting to Google Sheets...")
    client = await asyncio.to_thread(get_gspread_client)
    
    logger.info(f"Opening spreadsheet ID: {settings.sheet_id}")
    sheet = await asyncio.to_thread(client.open_by_key, settings.sheet_id)
    worksheet = await asyncio.to_thread(sheet.worksheet, settings.sheet_name)

    ticket_id = f"test-{uuid.uuid4().hex[:6]}"
    now_ts = datetime.now(timezone.utc).isoformat()

    # 1. Append
    row = [ticket_id, now_ts, now_ts, 123456789, "Test Name", "+123", "Test desc", "new", ""]
    await asyncio.to_thread(worksheet.append_row, row)
    logger.success(f"[1/3] Appended row {ticket_id}")

    # 2. Read back
    cell = await asyncio.to_thread(worksheet.find, ticket_id)
    if not cell:
        logger.error("Failed to find the appended row")
        return
    logger.success(f"[2/3] Found row at index {cell.row}")

    # 3. Update status and check delta
    t_before_update = datetime.now(timezone.utc).isoformat()
    await asyncio.to_thread(
        worksheet.update, 
        f"C{cell.row}:H{cell.row}", 
        [[t_before_update, 123456789, "Test Name", "+123", "Test desc", "in_progress"]]
    )
    logger.success(f"[3/3] Updated status to in_progress")

    # 4. Read delta
    all_records = await asyncio.to_thread(worksheet.get_all_records)
    delta = [
        r for r in all_records 
        if r.get("ticket_id") == ticket_id and r.get("updated_at") == t_before_update
    ]
    
    if delta:
        logger.success("Smoke test PASSED. Delta query logic works.")
    else:
        logger.error("Smoke test FAILED. Delta query did not catch the update.")


if __name__ == "__main__":
    asyncio.run(main())