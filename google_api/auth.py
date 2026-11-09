import gspread
from google.oauth2.service_account import Credentials

from config import settings

# Права доступа: чтение и запись в таблицы
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_gspread_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        str(settings.google_creds_path), scopes=SCOPES
    )
    return gspread.authorize(creds)