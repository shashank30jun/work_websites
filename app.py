"""
BSGP Book Redistribution Platform
Architecture: Clean Dynamic Page Router with Lazy-Loaded View Modules
"""

import importlib
import os
import streamlit as st
from dotenv import load_dotenv

from config import CONFIG, SCHEMA
from services.sheets_service import GoogleSheetsService

load_dotenv()

st.set_page_config(
    page_title=CONFIG.APP_TITLE,
    page_icon=CONFIG.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# 1. SERVICES & INITIALIZATION
# ==============================================================================


@st.cache_resource
def get_sheets_service():
    """Singleton Google Sheets API Service Handler."""
    return GoogleSheetsService(
        credentials_path=os.getenv(
            "GOOGLE_CREDENTIALS_PATH", "credentials.json"
        ),
        sheet_name=CONFIG.SHEET_NAME,
    )


def init_sheets(sheets_service):
    """Initializes sheet headers dynamically based on enabled feature flags."""
    try:
        targets = []
        if CONFIG.SHOW_HOME or CONFIG.SHOW_CATALOG:
            targets.extend(
                [
                    (CONFIG.WORKSHEET_MASTER_CATALOG, SCHEMA.CATALOG.headers),
                    (CONFIG.WORKSHEET_STOCK_LEDGER, SCHEMA.LEDGER.headers),
                ]
            )
        if CONFIG.SHOW_REQUEST:
            targets.append(
                (CONFIG.WORKSHEET_REQUESTS, SCHEMA.REQUESTS.headers)
            )
        if CONFIG.SHOW_SANSKAR:
            targets.append(
                (CONFIG.WORKSHEET_SANSKAR_LIST, SCHEMA.SANSKAR.headers)
            )

        # Core operational worksheet
        targets.append(
            (CONFIG.WORKSHEET_VOLUNTEERS, SCHEMA.VOLUNTEERS.headers)
        )

        for ws_name, headers in targets:
            sheets_service.ensure_headers(ws_name, headers)

    except Exception as e:
        st.error(f"Failed to initialize worksheets: {str(e)}")


# ==============================================================================
# 2. DYNAMIC PAGE REGISTRY & LAZY LOADER
# ==============================================================================

PAGE_REGISTRY = {
    "🏠 Home Dashboard": {
        "module": "views.home",
        "function": "render_home_dashboard",
        "enabled": CONFIG.SHOW_HOME,
    },
    "🕉️ Sanskar Registration": {
        "module": "views.sanskar",
        "function": "render_sanskar_registration",
        "enabled": CONFIG.SHOW_SANSKAR,
    },
    "📖 Book Catalog": {
        "module": "views.catalog",
        "function": "render_catalog",
        "enabled": CONFIG.SHOW_CATALOG,
    },
    "📝 Request a Book": {
        "module": "views.request",
        "function": "render_request_form",
        "enabled": CONFIG.SHOW_REQUEST,
    },
    "📊 Admin Dashboard": {
        "module": "views.admin",
        "function": "render_admin_dashboard",
        "enabled": CONFIG.SHOW_ADMIN,
    },
}


def load_and_render_view(page_title: str, sheets_service):
    """Executes target view function cleanly using standard Python import caching."""
    page_info = PAGE_REGISTRY.get(page_title)

    if not page_info or not page_info["enabled"]:
        st.error("⚠️ This module is disabled by system configuration.")
        return

    try:
        # Standard dynamic import (Python's internal sys.modules handles caching automatically)
        module = importlib.import_module(page_info["module"])
        view_fn = getattr(module, page_info["function"])
        view_fn(sheets_service)
    except Exception as e:
        st.error(f"⚠️ Error rendering view '{page_title}': {str(e)}")


# ==============================================================================
# 3. ROUTER & MAIN ENTRY POINT
# ==============================================================================


def render_sidebar():
    """Renders platform navigation sidebar with active routes only."""
    with st.sidebar:
        st.header("🕉️ BSGP Platform")
        st.caption("DSVV • Shantikunj")
        st.divider()

        active_pages = [
            title for title, page in PAGE_REGISTRY.items() if page["enabled"]
        ]

        if not active_pages:
            st.warning("No feature views are enabled in config.py")
            return None

        selected_page = st.radio(
            "Navigate", active_pages, label_visibility="collapsed"
        )

        st.divider()
        st.info(
            "**Quick Info**\n\n• Classes: 5 to 10\n• Exam: BSGP\n• Org: DSVV, Haridwar"
        )
        st.divider()
        st.caption("© 2026 DSVV")

        return selected_page


def main():
    st.title(f"{CONFIG.APP_ICON} {CONFIG.APP_TITLE}")
    st.caption(CONFIG.APP_SUBTITLE)
    st.divider()

    try:
        sheets_service = get_sheets_service()
        init_sheets(sheets_service)
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        st.stop()

    selected_page_title = render_sidebar()

    if selected_page_title:
        load_and_render_view(selected_page_title, sheets_service)


if __name__ == "__main__":
    main()
