"""
Book Request Form Component
"""

import streamlit as st
from datetime import datetime

from config import CONFIG
from models.book import Book
from models.request import BookRequest
from services.sheets_service import GoogleSheetsService
from utils.validators import validate_phone, sanitize_input


def render_request_form(sheets_service: GoogleSheetsService):
    book = st.session_state.get("selected_book")

    if not book:
        st.info("Please select a book from the catalog first.")
        return

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a3a2f, #2d5a4a); 
                border-radius: 14px; padding: 20px; color: white; margin-bottom: 20px;">
        <h3 style="margin:0; font-size:18px;">📖 Request Book</h3>
        <p style="margin:6px 0 0 0; opacity:0.9; font-size:14px;">
            {book.title} ({book.target_class}) by {book.author}
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("book_request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            requester_name = st.text_input("Your Name *", placeholder="Enter your full name")
            requester_contact = st.text_input("Phone Number *", placeholder="10-digit mobile number")
            requester_type = st.selectbox("You are a *", 
                ["Student", "Teacher", "School Coordinator", "Parent"])

        with col2:
            school_name = st.text_input("School / Organization Name", placeholder="Enter school name")
            class_needed = st.selectbox("Class Needed *", CONFIG.CLASSES)
            quantity = st.number_input("Quantity *", min_value=1, max_value=10, value=1)

        notes = st.text_area("Additional Notes", placeholder="Any specific requirements...", max_chars=300)

        volunteers = _get_active_volunteers(sheets_service)
        assigned_volunteer = st.selectbox("Preferred Volunteer (Optional)", 
            ["Auto-assign"] + [v["Name"] for v in volunteers])

        submitted = st.form_submit_button("Submit Request", use_container_width=True, type="primary")

        if submitted:
            errors = []

            if not requester_name or len(requester_name.strip()) < 2:
                errors.append("Please enter a valid name")

            valid_phone, phone_msg = validate_phone(requester_contact)
            if not valid_phone:
                errors.append(phone_msg)

            if errors:
                for err in errors:
                    st.error(err)
                return

            request_id = sheets_service.get_next_id(CONFIG.WORKSHEET_REQUESTS)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            request = BookRequest(
                request_id=request_id,
                timestamp=timestamp,
                book_id=book.book_id,
                book_title=book.title,
                requester_name=sanitize_input(requester_name),
                requester_contact=phone_msg,
                requester_type=requester_type,
                school_name=sanitize_input(school_name),
                class_needed=class_needed,
                quantity=int(quantity),
                status="Pending",
                assigned_volunteer=assigned_volunteer if assigned_volunteer != "Auto-assign" else "",
                delivery_date="",
                notes=sanitize_input(notes),
            )

            try:
                sheets_service.append_row(CONFIG.WORKSHEET_REQUESTS, request.to_row())
                _update_book_status(sheets_service, book.book_id, "Reserved")

                st.success(f"✅ Request submitted! Your Request ID: {request_id}")
                st.balloons()

                st.session_state.selected_book = None
                st.session_state.show_request_form = False

            except Exception as e:
                st.error(f"Failed to submit request: {str(e)}")


def _get_active_volunteers(sheets_service):
    try:
        records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)
        return [r for r in records if str(r.get("Is_Active", "")).lower() == "yes"]
    except:
        return []


def _update_book_status(sheets_service, book_id, status):
    records = sheets_service.get_all_records(CONFIG.WORKSHEET_INVENTORY, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Book_ID", "")) == book_id:
            sheets_service.update_cell(CONFIG.WORKSHEET_INVENTORY, idx, 12, status)
            break
