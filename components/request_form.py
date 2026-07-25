"""
Book Request Form Component
Updated: Works with Master Catalog + Stock Ledger architecture
"""

import streamlit as st
from datetime import datetime

from config import CONFIG
from models.master_catalog import MasterCatalogItem
from services.sheets_service import GoogleSheetsService
from utils.validators import validate_phone, sanitize_input


def render_request_form(sheets_service: GoogleSheetsService):
    item = st.session_state.get("selected_book")

    if not item:
        st.info("Please select a book from the catalog first.")
        return

    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a3a2f, #2d5a4a); 
                border-radius: 14px; padding: 20px; color: white; margin-bottom: 20px;">
        <h3 style="margin:0; font-size:18px;">📖 Request Book</h3>
        <p style="margin:6px 0 0 0; opacity:0.9; font-size:14px;">
            {item.title} ({item.target_class}) by {item.author}
        </p>
        <p style="margin:4px 0 0 0; opacity:0.7; font-size:12px;">
            {item.available_qty} copies available out of {item.total_qty} total
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("request_submitted", False):
        st.success(f"✅ Request submitted! Your Request ID: {st.session_state.get('last_request_id', '')}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Submit Another Request", width=True, type="primary"):
                st.session_state.request_submitted = False
                st.session_state.form_data = {}
                st.session_state.last_request_id = ""
                st.rerun()
        with col2:
            if st.button("📖 Back to Catalog", width=True):
                st.session_state.show_request_form = False
                st.session_state.selected_book = None
                st.session_state.request_submitted = False
                st.session_state.form_data = {}
                st.rerun()
        return

    with st.form("book_request_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            requester_name = st.text_input(
                "Your Name *", 
                value=st.session_state.form_data.get("requester_name", ""),
                placeholder="Enter your full name"
            )
            requester_contact = st.text_input(
                "Phone Number *", 
                value=st.session_state.form_data.get("requester_contact", ""),
                placeholder="10-digit mobile number"
            )
            requester_type = st.selectbox(
                "You are a *", 
                ["Student", "Teacher", "School Coordinator", "Parent", "Volunteer"],
                index=["Student", "Teacher", "School Coordinator", "Parent", "Volunteer"].index(
                    st.session_state.form_data.get("requester_type", "Student")
                ) if st.session_state.form_data.get("requester_type") in ["Student", "Teacher", "School Coordinator", "Parent", "Volunteer"] else 0
            )

        with col2:
            school_name = st.text_input(
                "School / Organization Name", 
                value=st.session_state.form_data.get("school_name", ""),
                placeholder="Enter school name"
            )
            class_needed = st.selectbox(
                "Class Needed *", 
                CONFIG.CLASSES,
                index=CONFIG.CLASSES.index(
                    st.session_state.form_data.get("class_needed", item.target_class)
                ) if st.session_state.form_data.get("class_needed") in CONFIG.CLASSES else 
                (CONFIG.CLASSES.index(item.target_class) if item.target_class in CONFIG.CLASSES else 0)
            )
            max_qty = min(item.available_qty, 10)
            quantity = st.number_input(
                "Quantity *", 
                min_value=1, max_value=max_qty, 
                value=min(st.session_state.form_data.get("quantity", 1), max_qty)
            )

        notes = st.text_area(
            "Additional Notes", 
            value=st.session_state.form_data.get("notes", ""),
            placeholder="Any specific requirements...", 
            max_chars=300
        )

        volunteers = _get_active_volunteers(sheets_service)
        volunteer_options = ["Auto-assign"] + [v["Name"] for v in volunteers]
        current_vol = st.session_state.form_data.get("assigned_volunteer", "Auto-assign")
        vol_index = volunteer_options.index(current_vol) if current_vol in volunteer_options else 0

        assigned_volunteer = st.selectbox(
            "Preferred Volunteer (Optional)", 
            volunteer_options,
            index=vol_index
        )

        submitted = st.form_submit_button("Submit Request", width=True, type="primary")

        if submitted:
            st.session_state.form_data = {
                "requester_name": requester_name,
                "requester_contact": requester_contact,
                "requester_type": requester_type,
                "school_name": school_name,
                "class_needed": class_needed,
                "quantity": int(quantity),
                "notes": notes,
                "assigned_volunteer": assigned_volunteer,
            }

            errors = []

            if not requester_name or len(requester_name.strip()) < 2:
                errors.append("Please enter a valid name (at least 2 characters)")

            valid_phone, phone_msg = validate_phone(requester_contact)
            if not valid_phone:
                errors.append(phone_msg)

            if int(quantity) > item.available_qty:
                errors.append(f"Only {item.available_qty} copies available. Please reduce quantity.")

            if errors:
                for err in errors:
                    st.error(err)
                st.stop()

            # Create request
            request_id = sheets_service.get_next_id(CONFIG.WORKSHEET_REQUESTS, prefix="REQ")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            request_row = [
                request_id, timestamp, item.catalog_id, item.title, class_needed,
                int(quantity), sanitize_input(requester_name), phone_msg, requester_type,
                sanitize_input(school_name), "Pending",
                assigned_volunteer if assigned_volunteer != "Auto-assign" else "",
                0, sanitize_input(notes)
            ]

            try:
                sheets_service.append_row(CONFIG.WORKSHEET_REQUESTS, request_row)

                # Update Master Catalog: reduce available, increase reserved
                _update_catalog_qty(sheets_service, item.catalog_id, int(quantity))

                st.session_state.form_data = {}
                st.session_state.request_submitted = True
                st.session_state.last_request_id = request_id
                st.rerun()

            except Exception as e:
                st.error(f"Failed to submit request: {str(e)}")
                st.stop()


def _get_active_volunteers(sheets_service):
    try:
        records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)
        return [r for r in records if str(r.get("Is_Active", "")).lower() == "yes"]
    except:
        return []


def _update_catalog_qty(sheets_service, catalog_id: str, qty: int):
    """Update Master Catalog quantities when a request is made."""
    records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Catalog_ID", "")) == catalog_id:
            available = int(record.get("Available_Qty", 0) or 0)
            reserved = int(record.get("Reserved_Qty", 0) or 0)

            # Update Available (col 9) and Reserved (col 11)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 9, available - qty)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 11, reserved + qty)
            break
