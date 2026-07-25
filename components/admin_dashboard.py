
"""
Admin Dashboard Component
Updated: Uses Master Catalog + Stock Ledger architecture
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import CONFIG
from models.master_catalog import MasterCatalogItem
from models.stock_ledger import StockLedgerItem
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
            cat_records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG)
            ledger_records = sheets_service.get_all_records(CONFIG.WORKSHEET_STOCK_LEDGER)
            req_records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS)
            vol_records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)

            catalog = [MasterCatalogItem.from_row(r) for r in cat_records]
            ledger = [StockLedgerItem.from_row(r) for r in ledger_records]
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            return

    st.markdown("### 📊 Overview")

    total_books = sum(c.total_qty for c in catalog)
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog)
    available = sum(c.available_qty for c in catalog)
    reserved = sum(c.reserved_qty for c in catalog)
    distributed = sum(c.distributed_qty for c in catalog)
    pending_reqs = sum(int(r.get("Qty_Requested", 0) or 0) for r in req_records if r.get("Request_Status") == "Pending")

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        _metric_card("Total Books", total_books, "📚")
    with m2:
        _metric_card("Total Cost", format_currency(total_cost), "💰")
    with m3:
        _metric_card("Available", available, "✅")
    with m4:
        _metric_card("Reserved", reserved, "📦")
    with m5:
        _metric_card("Pending Qty", pending_reqs, "⏳")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Distribution by Class")
        class_data = {}
        for c in catalog:
            class_data[c.target_class] = class_data.get(c.target_class, 0) + c.total_qty

        fig = go.Figure(data=[go.Pie(
            labels=list(class_data.keys()),
            values=list(class_data.values()),
            hole=0.5,
            marker_colors=['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#f44336', '#795548']
        )])
        fig.update_layout(showlegend=True, height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width=True)

    with col2:
        st.markdown("#### Status Distribution")
        fig = go.Figure(data=[go.Bar(
            x=["Available", "Reserved", "Distributed"],
            y=[available, reserved, distributed],
            marker_color=['#4caf50', '#ff9800', '#2196f3']
        )])
        fig.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width=True)

    st.divider()

    st.markdown("### 📋 Master Catalog")

    if catalog:
        cat_df = pd.DataFrame([{
            "ID": c.catalog_id,
            "Title": c.title,
            "Author": c.author,
            "Class": c.target_class,
            "Genre": c.genre,
            "Cost": c.formatted_cost,
            "Total": c.total_qty,
            "Available": c.available_qty,
            "Reserved": c.reserved_qty,
            "Distributed": c.distributed_qty,
            "Status": c.stock_status,
        } for c in catalog])
        st.dataframe(cat_df, width=True, hide_index=True)

    st.divider()

    st.markdown("### 📦 Stock Ledger (Individual Copies)")

    with st.expander("View All Copies"):
        if ledger:
            led_df = pd.DataFrame([{
                "Copy ID": l.copy_id,
                "Title": l.title,
                "Class": l.target_class,
                "Status": l.status,
                "Current Holder": l.current_holder,
                "Holder Type": l.holder_type,
                "Assigned": l.assigned_date,
                "Distributed": l.distributed_date,
            } for l in ledger])
            st.dataframe(led_df, width=True, hide_index=True)
        else:
            st.info("No individual copy records yet.")

    st.divider()

    st.markdown("### 📨 Pending Requests")

    pending = [r for r in req_records if r.get("Request_Status") == "Pending"]
    if pending:
        for req in pending:
            with st.container():
                cols = st.columns([2, 2, 1.5, 1, 1, 1])
                cols[0].markdown(f"**{req.get('Book_Title', '')}**")
                cols[1].markdown(f"{req.get('Requester_Name', '')}")
                cols[2].markdown(f"{req.get('School_Name', '')}")
                cols[3].markdown(f"Qty: {req.get('Qty_Requested', 0)}")

                if cols[4].button("✅ Approve", key=f"app_{req.get('Request_ID', '')}"):
                    _approve_request(sheets_service, req)
                    st.rerun()

                if cols[5].button("❌ Reject", key=f"rej_{req.get('Request_ID', '')}"):
                    _reject_request(sheets_service, req)
                    st.rerun()
    else:
        st.info("No pending requests.")

    st.divider()

    st.markdown("### 👥 Volunteer Activity")

    vol_df = pd.DataFrame([{
        "Name": v.get("Name", ""),
        "Type": v.get("Type", ""),
        "City": v.get("City", ""),
        "Holding": int(v.get("Books_Holding", 0) or 0),
        "Distributed Lifetime": int(v.get("Books_Distributed_Lifetime", 0) or 0),
        "Active": "✅" if str(v.get("Is_Active", "")).lower() == "yes" else "❌"
    } for v in vol_records])

    st.dataframe(vol_df, width=True, hide_index=True)

    st.markdown("### 💰 Cost Breakdown")
    cost_by_class = {}
    for c in catalog:
        cost_by_class[c.target_class] = cost_by_class.get(c.target_class, 0) + (c.total_qty * c.cost_per_unit)

    fig = go.Figure(data=[go.Bar(
        x=list(cost_by_class.keys()),
        y=list(cost_by_class.values()),
        marker_color='#2d5a4a'
    )])
    fig.update_layout(height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width=True)


def _metric_card(label, value, icon):
    st.markdown(f"""
    <div style="background:white; border-radius:12px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); text-align:center;">
        <div style="font-size:24px; margin-bottom:4px;">{icon}</div>
        <div style="font-size:22px; font-weight:700; color:#1a3a2f;">{value}</div>
        <div style="font-size:11px; color:#666; margin-top:2px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def _approve_request(sheets_service, req):
    req_id = req.get("Request_ID", "")
    catalog_id = req.get("Catalog_ID", "")
    qty = int(req.get("Qty_Requested", 0) or 0)
    volunteer = req.get("Assigned_Volunteer", "")

    records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Request_ID", "")) == req_id:
            sheets_service.update_cell(CONFIG.WORKSHEET_REQUESTS, idx, 11, "Approved")
            sheets_service.update_cell(CONFIG.WORKSHEET_REQUESTS, idx, 13, qty)
            break

    cat_records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG, use_cache=False)
    for idx, record in enumerate(cat_records, start=2):
        if str(record.get("Catalog_ID", "")) == catalog_id:
            reserved = int(record.get("Reserved_Qty", 0) or 0)
            dist = int(record.get("Distributed_Qty", 0) or 0)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 11, reserved - qty)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 10, dist + qty)
            break

    for i in range(qty):
        copy_id = sheets_service.get_next_copy_id(catalog_id, CONFIG.WORKSHEET_STOCK_LEDGER)
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d")
        ledger_row = [
            copy_id, catalog_id, req.get("Book_Title", ""), req.get("Class_Needed", ""),
            "In_Transit", volunteer or "Stock", "Volunteer" if volunteer else "Stock",
            now, "", "", "", "", f"Approved from request {req_id}"
        ]
        sheets_service.append_row(CONFIG.WORKSHEET_STOCK_LEDGER, ledger_row)


def _reject_request(sheets_service, req):
    req_id = req.get("Request_ID", "")
    catalog_id = req.get("Catalog_ID", "")
    qty = int(req.get("Qty_Requested", 0) or 0)

    records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Request_ID", "")) == req_id:
            sheets_service.update_cell(CONFIG.WORKSHEET_REQUESTS, idx, 11, "Rejected")
            break

    cat_records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG, use_cache=False)
    for idx, record in enumerate(cat_records, start=2):
        if str(record.get("Catalog_ID", "")) == catalog_id:
            available = int(record.get("Available_Qty", 0) or 0)
            reserved = int(record.get("Reserved_Qty", 0) or 0)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 9, available + qty)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 11, reserved - qty)
            break
