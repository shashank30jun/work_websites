"""
Home Dashboard View: Platform Inventory Overview & Metrics
"""

import pandas as pd
import streamlit as st

from config import CONFIG
from models.master_catalog import MasterCatalogItem
from models.stock_ledger import StockLedgerItem
from utils.formatters import format_currency


def render_home_dashboard(sheets_service):
    st.header("📊 Dashboard Overview")

    catalog = []
    ledger = []
    req_records = []

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

            if cat_records:
                catalog = [
                    MasterCatalogItem.from_row(r)
                    for r in cat_records
                    if isinstance(r, dict)
                ]
            if ledger_records:
                ledger = [
                    StockLedgerItem.from_row(r)
                    for r in ledger_records
                    if isinstance(r, dict)
                ]
        except Exception as e:
            st.error(f"Failed to load dashboard data: {str(e)}")

    # Metrics calculation with empty-list guards
    total_books = sum(c.total_qty for c in catalog) if catalog else 0
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog) if catalog else 0
    available_total = sum(c.available_qty for c in catalog) if catalog else 0

    copies_with_volunteers = len([l for l in ledger if l.is_with_volunteer])
    copies_with_teachers = len(
        [
            l
            for l in ledger
            if l.status == "In_Transit" and l.holder_type == "Teacher"
        ]
    )
    copies_distributed = len([l for l in ledger if l.is_distributed])

    schools = {
        r.get("School_Name")
        for r in req_records
        if isinstance(r, dict) and r.get("School_Name")
    }
    students_registered = sum(
        int(r.get("Qty_Requested", 0) or 0)
        for r in req_records
        if isinstance(r, dict) and r.get("Requester_Type") == "Student"
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
        st.dataframe(cat_df, width="stretch", hide_index=True)
    else:
        st.info("No catalog items available in Google Sheets.")
