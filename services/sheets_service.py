"""
Google Sheets Service - Thread-safe, rate-limited API wrapper
Updated: Supports Streamlit Secrets (st.secrets) & Master Catalog architecture
"""

import os
import time
import json
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

try:
    from googleapiclient.errors import HttpError
except ImportError:
    try:
        from google.api_core.exceptions import GoogleAPIError as HttpError
    except ImportError:
        class HttpError(Exception):
            def __init__(self, resp=None, content=None):
                self.resp = resp or type('obj', (object,), {'status': 500})()
                self.content = content
                super().__init__(str(content))


class RateLimiter:
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
            status = getattr(getattr(e, 'resp', None), 'status', 0)
            if status == 429:
                time.sleep(5)
                return func(self, *args, **kwargs)
            raise
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(5)
                return func(self, *args, **kwargs)
            raise
    return wrapper


class GoogleSheetsService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, sheet_name="BSGP_Book_Inventory"):
        if self._initialized:
            return

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

            # ✅ Pull GCP Service Account info natively from Streamlit secrets (.streamlit/secrets.toml)
            if "gcp_service_account" in st.secrets:
                creds_info = dict(st.secrets["gcp_service_account"])
            else:
                raise KeyError("Missing [gcp_service_account] block in .streamlit/secrets.toml")

            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
            self._client = gspread.authorize(credentials)
            self._spreadsheet = self._client.open(self.sheet_name)

            for ws in self._spreadsheet.worksheets():
                self._worksheets[ws.title] = ws

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Google Sheets via Streamlit Secrets: {str(e)}")

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

    @with_rate_limit
    def batch_update(self, worksheet_name: str, updates: List[tuple]):
        """Batch update multiple cells at once for efficiency."""
        ws = self._get_worksheet(worksheet_name)
        cells = [gspread.Cell(row, col, value) for row, col, value in updates]
        ws.update_cells(cells, value_input_option='USER_ENTERED')
        self._clear_cache(f"records_{worksheet_name}")

    def get_next_id(self, worksheet_name: str, id_column: int = 1, prefix: str = "BSGP") -> str:
        records = self.get_all_records(worksheet_name, use_cache=False)
        if not records:
            return f"{prefix}001"

        max_num = 0
        for record in records:
            id_val = str(record.get(list(record.keys())[id_column - 1], ""))
            if id_val.startswith(prefix):
                try:
                    num = int(id_val[len(prefix):])
                    max_num = max(max_num, num)
                except ValueError:
                    continue

        return f"{prefix}{max_num + 1:03d}"

    def get_next_copy_id(self, catalog_id: str, worksheet_name: str) -> str:
        """Generate next copy ID for a catalog item (e.g., CAT001-01, CAT001-02)."""
        records = self.get_all_records(worksheet_name, use_cache=False)
        max_num = 0
        for record in records:
            copy_id = str(record.get("Copy_ID", ""))
            if copy_id.startswith(f"{catalog_id}-"):
                try:
                    num = int(copy_id.split("-")[-1])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        return f"{catalog_id}-{max_num + 1:02d}"

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
