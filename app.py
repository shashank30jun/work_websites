"""
BSGP Book Redistribution Platform v2
Updated: Master Catalog + Stock Ledger architecture
"""

import os
import streamlit as st
from dotenv import load_dotenv

from config import (
    CONFIG, MASTER_CATALOG_HEADERS, STOCK_LEDGER_HEADERS,
    REQUESTS_HEADERS, DISTRIBUTION_HEADERS, VOLUNTEERS_HEADERS
)
from services.sheets_service import GoogleSheetsService
from components.home_dashboard import render_home_dashboard
from components.catalog import render_catalog
from components.request_form import render_request_form
from components.admin_dashboard import render_admin_dashboard

load_dotenv()

st.set_page_config(
    page_title=CONFIG.APP_TITLE,
    page_icon=CONFIG.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1a3a2f 0%, #2d5a4a 50%, #c9a227 100%);
        border-radius: 16px;
        padding: 28px;
        color: white;
        margin-bottom: 24px;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    div[data-testid="stForm"] {
        background: white;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #1a3a2f !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_sheets_service():
    return GoogleSheetsService(
        credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        sheet_name=CONFIG.SHEET_NAME
    )


def init_sheets(sheets_service):
    """Initialize all worksheets with proper headers."""
    try:
        sheets_service.ensure_headers(CONFIG.WORKSHEET_MASTER_CATALOG, MASTER_CATALOG_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_STOCK_LEDGER, STOCK_LEDGER_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_REQUESTS, REQUESTS_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_DISTRIBUTION, DISTRIBUTION_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_VOLUNTEERS, VOLUNTEERS_HEADERS)
    except Exception as e:
        st.error(f"Failed to initialize sheets: {str(e)}")


def render_header():
    st.markdown(f"""
    <div class="main-header">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="width:56px; height:56px; background:rgba(255,255,255,0.15); 
                        border-radius:12px; display:flex; align-items:center; justify-content:center; 
                        font-size:28px;">📚</div>
            <div>
                <h1 style="margin:0; font-size:26px; font-weight:700; letter-spacing:-0.5px;">
                    {CONFIG.APP_TITLE}
                </h1>
                <p style="margin:4px 0 0 0; opacity:0.85; font-size:14px;">
                    {CONFIG.APP_SUBTITLE}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:10px 0;">
            <div style="font-size:40px; margin-bottom:8px;">🕉️</div>
            <h3 style="margin:0; color:#1a3a2f; font-size:16px;">BSGP Platform</h3>
            <p style="margin:4px 0 0 0; font-size:11px; color:#666;">
                DSVV • Shantikunj
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        page = st.radio("Navigate", [
            "🏠 Home Dashboard",
            "📖 Book Catalog",
            "📝 Request a Book", 
            "📊 Admin Dashboard",
            "ℹ️ About BSGP"
        ], label_visibility="collapsed")

        st.divider()

        st.markdown("""
        <div style="background:#f8f6f1; border-radius:10px; padding:12px;">
            <p style="margin:0 0 8px 0; font-size:12px; font-weight:600; color:#1a3a2f;">
                🎯 Quick Info
            </p>
            <p style="margin:0; font-size:11px; color:#666; line-height:1.6;">
                • Classes: 5 to 10<br>
                • Exam: BSGP<br>
                • Org: DSVV, Haridwar
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("<p style='font-size:10px; color:#999; text-align:center;'>© 2024 DSVV</p>", 
                   unsafe_allow_html=True)

        return page


def render_about():
    st.markdown("""
    ### 🕉️ About BSGP

    **Bharatiya Sanskriti Gyaan Pariksha (BSGP)** is a unique initiative by 
    **Dev Sanskriti Vishwavidyalaya (DSVV)**, Shantikunj, Haridwar.

    #### Purpose
    BSGP is conducted for students of **Classes 5 to 10** to:
    - Awaken cultural values and patriotism
    - Build character, confidence, and self-awareness
    - Connect the young generation with India's glorious heritage

    #### This Platform
    - 📚 **Master Catalog** — Unique titles with quantities
    - 📦 **Stock Ledger** — Individual copy tracking
    - 🔄 **Distribution Log** — Every handover recorded
    - 👥 **Volunteer coordination**

    ---
    *"संस्कृति रक्षणम्, चरित्र निर्माणम्"*
    """)


def main():
    render_header()

    # Initialize session state
    for key, default in [
        ("selected_book", None),
        ("show_request_form", False),
        ("request_submitted", False),
        ("form_data", {}),
        ("last_request_id", ""),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    try:
        sheets_service = get_sheets_service()
        init_sheets(sheets_service)
    except Exception as e:
        st.error(f"""
        ⚠️ **Connection Error**

        Could not connect to Google Sheets. Please check:
        1. Your `credentials.json` file is present
        2. The Google Sheet '{CONFIG.SHEET_NAME}' exists and is shared with the service account
        3. Google Sheets API is enabled

        Error: {str(e)}
        """)
        st.stop()

    page = render_sidebar()

    if "Home" in page:
        render_home_dashboard(sheets_service)
    elif "Catalog" in page:
        render_catalog(sheets_service)
    elif "Request" in page:
        if not st.session_state.get("selected_book"):
            st.info("📖 Please select a book from the **Book Catalog** first.")
            if st.button("Go to Book Catalog →", type="primary"):
                st.rerun()
        else:
            render_request_form(sheets_service)
            if not st.session_state.get("request_submitted", False):
                if st.button("← Back to Catalog", width=True):
                    st.session_state.show_request_form = False
                    st.session_state.selected_book = None
                    st.session_state.form_data = {}
                    st.rerun()
    elif "Admin" in page:
        render_admin_dashboard(sheets_service)
    elif "About" in page:
        render_about()


if __name__ == "__main__":
    main()
