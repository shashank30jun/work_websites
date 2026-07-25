"""
Book Request Form View: Individual Book Ordering
"""

from datetime import datetime
import streamlit as st

from config import CONFIG
from utils.validators import sanitize_input, validate_phone


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
