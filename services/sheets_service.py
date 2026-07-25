"""
Google Sheets Service - Thread-safe, rate-limited API wrapper
"""

import os
import time
import json
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError


class RateLimiter:
    """Thread-safe rate limiter for Google Sheets API."""

    def __init__(self, max_calls: int = 60, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = datetime.now()
            self.calls = [c for c in self.calls if now - c < timedelta(seconds=self.window_seconds)]
            if len(self.calls) >= self.max_calls:
                return False
            self.calls.append(now)
            return True

    def wait_and_acquire(self, backoff: float = 2.0):
        while not self.acquire():
            time.sleep(backoff)


def with_rate_limit(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.rate_limiter.wait_and_acquire()
        try:
            return func(self, *args, **kwargs)
        except HttpError as e:
            if e.resp.status == 429:
                time.sleep(5)
                return func(self, *args, **kwargs)
            raise
    return wrapper


class GoogleSheetsService:
    """Production-grade Google Sheets service."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, credentials_path=None, sheet_name="BSGP_Book_Inventory"):
        if self._initialized:
            return

        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        self.sheet_name = sheet_name
        self.rate_limiter = RateLimiter(max_calls=60, window_seconds=60)
        self._client = None
        self._spreadsheet = None
        self._worksheets = {}
        self._cache = {}
        self._cache_ttl = 30
        self._cache_lock = threading.Lock()

        self._connect()
        self._initialized = True

    def _connect(self):
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            creds_data = self.credentials_path
            if os.path.exists(self.credentials_path):
                with open(self.credentials_path, 'r') as f:
                    creds_data = f.read()
            elif creds_data.startswith('{'):
                pass
            else:
                env_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
                if env_creds:
                    creds_data = env_creds
                else:
                    raise FileNotFoundError(f"Credentials not found at {self.credentials_path}")

            creds_info = json.loads(creds_data) if isinstance(creds_data, str) else creds_data
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
            self._client = gspread.authorize(credentials)
            self._spreadsheet = self._client.open(self.sheet_name)

            for ws in self._spreadsheet.worksheets():
                self._worksheets[ws.title] = ws

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Google Sheets: {str(e)}")

    def _get_worksheet(self, name: str):
        if name not in self._worksheets:
            try:
                self._worksheets[name] = self._spreadsheet.worksheet(name)
            except gspread.WorksheetNotFound:
                self._worksheets[name] = self._spreadsheet.add_worksheet(
                    title=name, rows=1000, cols=20
                )
        return self._worksheets[name]

    def _get_from_cache(self, key: str):
        with self._cache_lock:
            if key in self._cache:
                timestamp, data = self._cache[key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                    return data
                del self._cache[key]
            return None

    def _set_cache(self, key: str, data: Any):
        with self._cache_lock:
            self._cache[key] = (datetime.now(), data)

    def _clear_cache(self, pattern=None):
        with self._cache_lock:
            if pattern:
                keys_to_remove = [k for k in self._cache if pattern in k]
                for k in keys_to_remove:
                    del self._cache[k]
            else:
                self._cache.clear()

    @with_rate_limit
    def get_all_records(self, worksheet_name: str, use_cache: bool = True):
        cache_key = f"records_{worksheet_name}"
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        ws = self._get_worksheet(worksheet_name)
        records = ws.get_all_records()
        self._set_cache(cache_key, records)
        return records

    @with_rate_limit
    def append_row(self, worksheet_name: str, row: List, clear_cache: bool = True):
        ws = self._get_worksheet(worksheet_name)
        ws.append_row(row, value_input_option='USER_ENTERED')
        if clear_cache:
            self._clear_cache(f"records_{worksheet_name}")

    @with_rate_limit
    def update_cell(self, worksheet_name: str, row: int, col: int, value: Any):
        ws = self._get_worksheet(worksheet_name)
        ws.update_cell(row, col, value)
        self._clear_cache(f"records_{worksheet_name}")

    @with_rate_limit
    def update_row(self, worksheet_name: str, row_idx: int, row_data: List):
        ws = self._get_worksheet(worksheet_name)
        end_col = chr(64 + len(row_data))
        cell_range = f"A{row_idx}:{end_col}{row_idx}"
        ws.update(cell_range, [row_data], value_input_option='USER_ENTERED')
        self._clear_cache(f"records_{worksheet_name}")

    def get_next_id(self, worksheet_name: str, id_column: int = 1) -> str:
        records = self.get_all_records(worksheet_name, use_cache=False)
        if not records:
            return "BSGP001"

        max_num = 0
        for record in records:
            id_val = str(record.get(list(record.keys())[id_column - 1], ""))
            if id_val.startswith("BSGP"):
                try:
                    num = int(id_val[4:])
                    max_num = max(max_num, num)
                except ValueError:
                    continue

        return f"BSGP{max_num + 1:03d}"

    def ensure_headers(self, worksheet_name: str, headers: List[str]):
        ws = self._get_worksheet(worksheet_name)
        existing = ws.row_values(1)

        if not existing or existing[0] != headers[0]:
            ws.clear()
            ws.append_row(headers, value_input_option='USER_ENTERED')
            self._clear_cache(f"records_{worksheet_name}")

    def refresh_connection(self):
        self._connect()
        self._clear_cache()
