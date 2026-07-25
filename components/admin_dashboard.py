"""
Admin Dashboard Component
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import CONFIG
from models.book import Book
from models.request import BookRequest
from services.sheets_service import GoogleSheetsService
from utils.formatters import format_currency


def render_admin_dashboard(sheets_service: GoogleSheetsService):
    if not st.session_state.get("admin_authenticated", False):
        with st.form("admin_login"):
            st.markdown("### 🔐 Admin Login")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if password == st.secrets.get("ADMIN_PASSWORD", "bsgp2024"):
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    with st.spinner("Loading dashboard data..."):
        try:
            inv_records = sheets_service.get_all_records(CONFIG.WORKSHEET_INVENTORY)
            req_records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS)
            vol_records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)

            books = [Book.from_row(r) for r in inv_records]
            requests = [BookRequest.from_row(r) for r in req_records]
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            return

    st.markdown("### 📊 Overview")

    m1, m2, m3, m4, m5 = st.columns(5)

    total_books = len(books)
    total_cost = sum(b.cost_inr for b in books)
    available = len([b for b in books if b.status == "Available"])
    distributed = len([b for b in books if b.status == "Distributed"])
    pending_reqs = len([r for r in requests if r.status == "Pending"])

    with m1:
        _metric_card("Total Books", total_books, "📚")
    with m2:
        _metric_card("Total Cost", format_currency(total_cost), "💰")
    with m3:
        _metric_card("Available", available, "✅")
    with m4:
        _metric_card("Distributed", distributed, "🚚")
    with m5:
        _metric_card("Pending Requests", pending_reqs, "⏳")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Distribution by Class")
        class_data = {}
        for b in books:
            class_data[b.target_class] = class_data.get(b.target_class, 0) + 1

        fig = go.Figure(data=[go.Pie(
            labels=list(class_data.keys()),
            values=list(class_data.values()),
            hole=0.5,
            marker_colors=['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#f44336', '#795548']
        )])
        fig.update_layout(showlegend=True, height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Status Distribution")
        status_data = {}
        for b in books:
            status_data[b.status] = status_data.get(b.status, 0) + 1

        fig = go.Figure(data=[go.Bar(
            x=list(status_data.keys()),
            y=list(status_data.values()),
            marker_color=['#4caf50', '#ff9800', '#2196f3']
        )])
        fig.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.markdown("### 📋 Inventory Management")

    st.markdown("#### Quick Status Toggle")
    toggle_col1, toggle_col2, toggle_col3 = st.columns([2, 1, 1])

    with toggle_col1:
        book_options = {f"{b.title} ({b.book_id})": b for b in books}
        selected = st.selectbox("Select Book", list(book_options.keys()))

    with toggle_col2:
        new_status = st.selectbox("New Status", CONFIG.STATUS_ALL)

    with toggle_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Update Status", use_container_width=True, type="primary"):
            book = book_options[selected]
            try:
                _update_book_status(sheets_service, book.book_id, new_status)
                st.success(f"Updated {book.title} to {new_status}")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with st.expander("View Full Inventory"):
        df = pd.DataFrame([{
            "ID": b.book_id,
            "Title": b.title,
            "Author": b.author,
            "Class": b.target_class,
            "Genre": b.genre,
            "Cost": b.formatted_cost,
            "Status": b.status,
            "Volunteer": b.assigned_volunteer or "—",
            "Location": b.current_location or "—",
        } for b in books])
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 📨 Pending Requests")

    pending = [r for r in requests if r.status == "Pending"]
    if pending:
        for req in pending:
            with st.container():
                cols = st.columns([3, 2, 2, 2, 1, 1])
                cols[0].markdown(f"**{req.book_title}**")
                cols[1].markdown(f"{req.requester_name}")
                cols[2].markdown(f"{req.class_needed}")
                cols[3].markdown(f"Qty: {req.quantity}")

                if cols[4].button("✅ Approve", key=f"app_{req.request_id}"):
                    _update_request_status(sheets_service, req.request_id, "Approved")
                    st.rerun()

                if cols[5].button("❌ Reject", key=f"rej_{req.request_id}"):
                    _update_request_status(sheets_service, req.request_id, "Rejected")
                    _update_book_status(sheets_service, req.book_id, "Available")
                    st.rerun()
    else:
        st.info("No pending requests.")

    st.divider()

    st.markdown("### 👥 Volunteer Activity")

    vol_df = pd.DataFrame([{
        "Name": v.get("Name", ""),
        "Type": v.get("Type", ""),
        "City": v.get("City", ""),
        "Books Distributed": int(v.get("Books_Distributed", 0) or 0),
        "Active": "✅" if str(v.get("Is_Active", "")).lower() == "yes" else "❌"
    } for v in vol_records])

    st.dataframe(vol_df, use_container_width=True, hide_index=True)

    st.markdown("### 💰 Cost Breakdown")
    cost_by_genre = {}
    for b in books:
        cost_by_genre[b.genre] = cost_by_genre.get(b.genre, 0) + b.cost_inr

    fig = go.Figure(data=[go.Bar(
        x=list(cost_by_genre.keys()),
        y=list(cost_by_genre.values()),
        marker_color='#2d5a4a'
    )])
    fig.update_layout(height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _metric_card(label, value, icon):
    st.markdown(f"""
    <div style="background:white; border-radius:12px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); text-align:center;">
        <div style="font-size:24px; margin-bottom:4px;">{icon}</div>
        <div style="font-size:22px; font-weight:700; color:#1a3a2f;">{value}</div>
        <div style="font-size:11px; color:#666; margin-top:2px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def _update_book_status(sheets_service, book_id, status):
    records = sheets_service.get_all_records(CONFIG.WORKSHEET_INVENTORY, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Book_ID", "")) == book_id:
            sheets_service.update_cell(CONFIG.WORKSHEET_INVENTORY, idx, 12, status)
            break


def _update_request_status(sheets_service, request_id, status):
    records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Request_ID", "")) == request_id:
            sheets_service.update_cell(CONFIG.WORKSHEET_REQUESTS, idx, 11, status)
            break
