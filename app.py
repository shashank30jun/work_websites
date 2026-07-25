"""
BSGP Book Redistribution Platform
Architecture: Dynamic Page Router with Configurable Feature Toggles
"""

from datetime import datetime
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from config import (
    CONFIG,
    DISTRIBUTION_HEADERS,
    MASTER_CATALOG_HEADERS,
    REQUESTS_HEADERS,
    SANSKAR_HEADERS,
    STOCK_LEDGER_HEADERS,
    VOLUNTEERS_HEADERS,
)
from models.master_catalog import MasterCatalogItem
from models.sanskar_list import SanskarRecord
from models.stock_ledger import StockLedgerItem
from services.sheets_service import GoogleSheetsService
from utils.formatters import format_currency
from utils.validators import sanitize_input, validate_phone

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
    return GoogleSheetsService(
        credentials_path=os.getenv(
            "GOOGLE_CREDENTIALS_PATH", "credentials.json"
        ),
        sheet_name=CONFIG.SHEET_NAME,
    )


def init_sheets(sheets_service):
    try:
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_MASTER_CATALOG, MASTER_CATALOG_HEADERS
        )
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_STOCK_LEDGER, STOCK_LEDGER_HEADERS
        )
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_REQUESTS, REQUESTS_HEADERS
        )
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_DISTRIBUTION, DISTRIBUTION_HEADERS
        )
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_VOLUNTEERS, VOLUNTEERS_HEADERS
        )
        sheets_service.ensure_headers(
            CONFIG.WORKSHEET_SANSKAR_LIST, SANSKAR_HEADERS
        )
    except Exception as e:
        st.error(f"Failed to initialize sheets: {str(e)}")


def _get_active_volunteers(sheets_service):
    try:
        records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)
        return [
            r for r in records if str(r.get("Is_Active", "")).lower() == "yes"
        ]
    except Exception:
        return []


# ==============================================================================
# 2. PAGE VIEWS
# ==============================================================================


def render_home_dashboard(sheets_service):
    st.header("📊 Dashboard Overview")

    with st.spinner("Loading dashboard..."):
        try:
            cat_records = sheets_service.get_all_records(
                CONFIG.WORKSHEET_MASTER_CATALOG
            )
            ledger_records = sheets_service.get_all_records(
                CONFIG.WORKSHEET_STOCK_LEDGER
            )
            req_records = sheets_service.get_all_records(
                CONFIG.WORKSHEET_REQUESTS
            )

            catalog = [MasterCatalogItem.from_row(r) for r in cat_records]
            ledger = [StockLedgerItem.from_row(r) for r in ledger_records]
        except Exception as e:
            st.error(f"Failed to load dashboard: {str(e)}")
            return

    # Metrics calculation
    total_books = sum(c.total_qty for c in catalog)
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog)
    available_total = sum(c.available_qty for c in catalog)

    copies_with_volunteers = len([l for l in ledger if l.is_with_volunteer])
    copies_with_teachers = len(
        [
            l
            for l in ledger
            if l.status == "In_Transit" and l.holder_type == "Teacher"
        ]
    )
    copies_distributed = len([l for l in ledger if l.is_distributed])

    schools = {r.get("School_Name") for r in req_records if r.get("School_Name")}
    students_registered = sum(
        int(r.get("Qty_Requested", 0) or 0)
        for r in req_records
        if r.get("Requester_Type") == "Student"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Books", f"{total_books:,}", f"{format_currency(total_cost)} value"
    )
    col2.metric("Available", f"{available_total:,}", "In stock")
    col3.metric(
        "In Transit",
        f"{copies_with_volunteers + copies_with_teachers:,}",
        "With volunteers/teachers",
    )
    col4.metric("Distributed", f"{copies_distributed:,}", "To students")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Schools", f"{len(schools)}")
    col6.metric("Students", f"{students_registered}")
    col7.metric("With Teachers", f"{copies_with_teachers}")
    col8.metric("With Volunteers", f"{copies_with_volunteers}")

    st.divider()

    st.subheader("📚 Books Inventory by Title")
    if catalog:
        cat_df = pd.DataFrame(
            [
                {
                    "Title": c.title,
                    "Class": c.target_class,
                    "Genre": c.genre,
                    "Cost/Unit": c.formatted_cost,
                    "Total Qty": c.total_qty,
                    "Available": c.available_qty,
                    "Reserved": c.reserved_qty,
                    "Distributed": c.distributed_qty,
                    "Status": c.stock_status,
                }
                for c in sorted(catalog, key=lambda x: x.title)
            ]
        )
        st.dataframe(cat_df, use_container_width=True, hide_index=True)


def render_sanskar_registration(sheets_service):
    st.header("🕉️ Sanskar Event Registration")
    st.caption("Register cultural, spiritual, and educational Sanskar events.")

    with st.form("sanskar_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sanskar_name = st.text_input(
                "Sanskar Name *",
                placeholder="e.g., Naamkaran, Vidyarambha, Birthday",
            )
            occasion = st.text_input(
                "Occasion *", placeholder="Reason or context of event"
            )
            requester_name = st.text_input(
                "Requester Name *", placeholder="Full name"
            )

        with col2:
            requester_contact = st.text_input(
                "Contact Number *", placeholder="10-digit mobile number"
            )
            requester_type = st.selectbox(
                "Requester Type",
                ["Student", "Teacher", "Parent", "Volunteer", "Other"],
            )
            no_of_people = st.number_input(
                "Expected Attendance", min_value=1, value=10
            )

        volunteers = _get_active_volunteers(sheets_service)
        vol_options = ["Auto-assign"] + [v.get("Name", "") for v in volunteers]
        assigned_volunteer = st.selectbox(
            "Assigned Volunteer (Optional)", vol_options
        )

        notes = st.text_area("Event Notes", max_chars=300)
        submitted = st.form_submit_button("Register Sanskar", type="primary")

        if submitted:
            errors = []
            if not sanskar_name.strip():
                errors.append("Sanskar Name is required.")
            if not requester_name.strip():
                errors.append("Requester Name is required.")

            valid_phone, phone_msg = validate_phone(requester_contact)
            if not valid_phone:
                errors.append(phone_msg)

            if errors:
                for err in errors:
                    st.error(err)
            else:
                record = SanskarRecord(
                    sanskar_name=sanitize_input(sanskar_name),
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    occasion=sanitize_input(occasion),
                    requester_name=sanitize_input(requester_name),
                    requester_contact=phone_msg,
                    requester_type=requester_type,
                    no_of_people=str(no_of_people),
                    status="Pending",
                    assigned_volunteer=(
                        assigned_volunteer
                        if assigned_volunteer != "Auto-assign"
                        else ""
                    ),
                    notes=sanitize_input(notes),
                )

                try:
                    sheets_service.append_row(
                        CONFIG.WORKSHEET_SANSKAR_LIST, record.to_row()
                    )
                    st.success("✅ Sanskar event registered successfully!")
                except Exception as e:
                    st.error(f"Failed to submit: {str(e)}")


def render_catalog(sheets_service):
    st.header("📖 Book Catalog")

    try:
        records = sheets_service.get_all_records(
            CONFIG.WORKSHEET_MASTER_CATALOG
        )
        catalog = [MasterCatalogItem.from_row(r) for r in records]
    except Exception as e:
        st.error(f"Failed to load catalog: {str(e)}")
        return

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input(
            "🔍 Search", placeholder="Title, Author, or Genre..."
        )
    with col2:
        class_filter = st.selectbox("Class", ["All"] + CONFIG.CLASSES)
    with col3:
        status_filter = st.selectbox(
            "Stock Status", ["All", "In Stock", "Low Stock", "Out of Stock"]
        )

    filtered = catalog
    if search:
        s = search.lower()
        filtered = [
            c
            for c in filtered
            if s in c.title.lower()
            or s in c.author.lower()
            or s in c.genre.lower()
        ]
    if class_filter != "All":
        filtered = [c for c in filtered if c.target_class == class_filter]
    if status_filter != "All":
        filtered = [c for c in filtered if c.stock_status == status_filter]

    st.caption(f"Showing {len(filtered)} titles")

    for i in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j in range(3):
            idx = i + j
            if idx >= len(filtered):
                break
            item = filtered[idx]
            with cols[j]:
                with st.container(border=True):
                    st.write(f"**{item.title}**")
                    st.caption(f"by {item.author}")
                    st.write(f"📚 {item.target_class} • {item.formatted_cost}")

                    if item.is_in_stock:
                        if st.button(
                            "Request Book",
                            key=f"req_{item.catalog_id}",
                            type="primary",
                        ):
                            st.session_state.selected_book = item
                            st.session_state.show_request_form = True
                            st.rerun()
                    else:
                        st.button(
                            "Out of Stock",
                            key=f"out_{item.catalog_id}",
                            disabled=True,
                        )


def render_request_form(sheets_service):
    item = st.session_state.get("selected_book")
    if not item:
        st.info("Please select a book from the catalog first.")
        return

    st.header(f"📖 Request Book: {item.title}")

    with st.form("book_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            requester_name = st.text_input("Your Name *")
            requester_contact = st.text_input("Phone Number *")
            requester_type = st.selectbox(
                "You are a *", ["Student", "Teacher", "Parent", "Volunteer"]
            )

        with col2:
            school_name = st.text_input("School Name")
            class_needed = st.selectbox(
                "Class Needed *",
                CONFIG.CLASSES,
                index=(
                    CONFIG.CLASSES.index(item.target_class)
                    if item.target_class in CONFIG.CLASSES
                    else 0
                ),
            )
            quantity = st.number_input(
                "Quantity *", min_value=1, max_value=max(1, item.available_qty)
            )

        notes = st.text_area("Notes", max_chars=300)
        submitted = st.form_submit_button("Submit Request", type="primary")

        if submitted:
            valid_phone, phone_msg = validate_phone(requester_contact)
            if not requester_name or not valid_phone:
                st.error("Please enter a valid name and phone number.")
                return

            req_id = sheets_service.get_next_id(
                CONFIG.WORKSHEET_REQUESTS, prefix="REQ"
            )
            row = [
                req_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                item.catalog_id,
                item.title,
                class_needed,
                int(quantity),
                sanitize_input(requester_name),
                phone_msg,
                requester_type,
                sanitize_input(school_name),
                "Pending",
                "",
                0,
                sanitize_input(notes),
            ]

            try:
                sheets_service.append_row(CONFIG.WORKSHEET_REQUESTS, row)
                st.success(f"✅ Request submitted! ID: {req_id}")
            except Exception as e:
                st.error(f"Failed to submit: {str(e)}")


def render_admin_dashboard(sheets_service):
    st.header("📊 Admin Dashboard")
    st.info("Admin features enabled.")


def render_about():
    st.header("🕉️ About BSGP")
    st.write("""
    **Bharatiya Sanskriti Gyaan Pariksha (BSGP)** is a cultural initiative by 
    **Dev Sanskriti Vishwavidyalaya (DSVV)**, Shantikunj, Haridwar.
    """)


# ==============================================================================
# 3. DYNAMIC ROUTER & PAGE CONTROL
# ==============================================================================

# Master Registry of all available pages
PAGE_REGISTRY = {
    "🏠 Home Dashboard": {
        "view": render_home_dashboard,
        "enabled": getattr(CONFIG, "SHOW_HOME", True),
    },
    "🕉️ Sanskar Registration": {
        "view": render_sanskar_registration,
        "enabled": getattr(CONFIG, "SHOW_SANSKAR", True),
    },
    "📖 Book Catalog": {
        "view": render_catalog,
        "enabled": getattr(CONFIG, "SHOW_CATALOG", True),
    },
    "📝 Request a Book": {
        "view": render_request_form,
        "enabled": getattr(CONFIG, "SHOW_REQUEST", True),
    },
    "📊 Admin Dashboard": {
        "view": render_admin_dashboard,
        "enabled": getattr(CONFIG, "SHOW_ADMIN", True),
    },
    "ℹ️ About BSGP": {
        "view": render_about,
        "enabled": getattr(CONFIG, "SHOW_ABOUT", True),
    },
}


def render_header():
    st.title(f"{CONFIG.APP_ICON} {CONFIG.APP_TITLE}")
    st.caption(CONFIG.APP_SUBTITLE)
    st.divider()


def render_sidebar():
    with st.sidebar:
        st.header("🕉️ BSGP Platform")
        st.caption("DSVV • Shantikunj")
        st.divider()

        # Dynamically filter only enabled pages!
        active_pages = [
            title
            for title, page in PAGE_REGISTRY.items()
            if page["enabled"]
        ]

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
    render_header()

    try:
        sheets_service = get_sheets_service()
        init_sheets(sheets_service)
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        st.stop()

    # Route dynamically
    selected_page_title = render_sidebar()
    view_function = PAGE_REGISTRY[selected_page_title]["view"]

    # Render selected view
    view_function(sheets_service)


if __name__ == "__main__":
    main()
