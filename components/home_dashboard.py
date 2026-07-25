"""
Home Dashboard Component
Updated: Uses Master Catalog + Stock Ledger architecture
Shows: Total qty per title, available, with volunteers, distributed
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import CONFIG
from models.master_catalog import MasterCatalogItem
from models.stock_ledger import StockLedgerItem
from services.sheets_service import GoogleSheetsService
from utils.formatters import format_currency


def render_home_dashboard(sheets_service: GoogleSheetsService):
    st.markdown("""
    <style>
    .home-metric-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        text-align: center;
        height: 100%;
    }
    .home-metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #1a3a2f;
    }
    .home-metric-label {
        font-size: 12px;
        color: #666;
        margin-top: 4px;
    }
    .home-metric-sub {
        font-size: 11px;
        color: #888;
        margin-top: 2px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1a3a2f;
        margin: 24px 0 16px 0;
    }
    .insight-card {
        background: #f8f6f1;
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #2d5a4a;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.spinner("Loading dashboard..."):
        try:
            cat_records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG)
            ledger_records = sheets_service.get_all_records(CONFIG.WORKSHEET_STOCK_LEDGER)
            req_records = sheets_service.get_all_records(CONFIG.WORKSHEET_REQUESTS)
            vol_records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)

            catalog = [MasterCatalogItem.from_row(r) for r in cat_records]
            ledger = [StockLedgerItem.from_row(r) for r in ledger_records]
        except Exception as e:
            st.error(f"Failed to load dashboard: {str(e)}")
            return

    # ==================== CALCULATE METRICS ====================

    # From Master Catalog (quantity-level)
    total_books = sum(c.total_qty for c in catalog)
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog)
    available_total = sum(c.available_qty for c in catalog)
    reserved_total = sum(c.reserved_qty for c in catalog)
    distributed_total = sum(c.distributed_qty for c in catalog)

    # From Stock Ledger (individual copy-level tracking)
    copies_with_volunteers = [l for l in ledger if l.is_with_volunteer]
    copies_with_teachers = [l for l in ledger if l.status == "In_Transit" and l.holder_type == "Teacher"]
    copies_distributed = [l for l in ledger if l.is_distributed]

    # Volunteer holdings from ledger
    volunteer_holdings = {}
    teacher_holdings = {}
    for item in ledger:
        if item.status == "In_Transit":
            if item.holder_type == "Volunteer":
                volunteer_holdings[item.current_holder] = volunteer_holdings.get(item.current_holder, 0) + 1
            elif item.holder_type == "Teacher":
                teacher_holdings[item.current_holder] = teacher_holdings.get(item.current_holder, 0) + 1

    # Requests
    total_requests = len(req_records)
    pending_requests = sum(int(r.get("Qty_Requested", 0) or 0) for r in req_records if r.get("Request_Status") == "Pending")

    # Schools and students
    schools = set()
    students_registered = 0
    for r in req_records:
        if r.get("School_Name"):
            schools.add(r.get("School_Name"))
        if r.get("Requester_Type") == "Student":
            students_registered += int(r.get("Qty_Requested", 0) or 0)

    # ==================== TOP METRICS ROW ====================
    st.markdown("<h2 style='color:#1a3a2f; margin-bottom:20px;'>📊 Dashboard Overview</h2>", 
                unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value">{total_books}</div>
            <div class="home-metric-label">Total Books (All Copies)</div>
            <div class="home-metric-sub">{format_currency(total_cost)} total value</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#4caf50;">{available_total}</div>
            <div class="home-metric-label">Available in Stock</div>
            <div class="home-metric-sub">Ready to distribute</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        in_transit = len(copies_with_volunteers) + len(copies_with_teachers)
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#ff9800;">{in_transit}</div>
            <div class="home-metric-label">Books In Transit</div>
            <div class="home-metric-sub">With volunteers & teachers</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#2196f3;">{len(copies_distributed)}</div>
            <div class="home-metric-label">Distributed to Students</div>
            <div class="home-metric-sub">Successfully delivered</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Second row
    m5, m6, m7, m8 = st.columns(4)

    with m5:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#9c27b0;">{len(schools)}</div>
            <div class="home-metric-label">Schools Registered</div>
            <div class="home-metric-sub">Active participants</div>
        </div>
        """, unsafe_allow_html=True)

    with m6:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#f44336;">{students_registered}</div>
            <div class="home-metric-label">Students Registered</div>
            <div class="home-metric-sub">Total book requests</div>
        </div>
        """, unsafe_allow_html=True)

    with m7:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#795548;">{len(copies_with_teachers)}</div>
            <div class="home-metric-label">With Teachers</div>
            <div class="home-metric-sub">Books held by teachers</div>
        </div>
        """, unsafe_allow_html=True)

    with m8:
        st.markdown(f"""
        <div class="home-metric-card">
            <div class="home-metric-value" style="color:#2d5a4a;">{len(copies_with_volunteers)}</div>
            <div class="home-metric-label">With Volunteers</div>
            <div class="home-metric-sub">Books held by volunteers</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ==================== BOOKS BY TITLE WITH QTY ====================
    st.markdown("<div class='section-title'>📚 Books Inventory by Title</div>", unsafe_allow_html=True)

    if catalog:
        cat_df = pd.DataFrame([{
            "Title": c.title,
            "Class": c.target_class,
            "Genre": c.genre,
            "Cost/Unit": c.formatted_cost,
            "Total Qty": c.total_qty,
            "Available": c.available_qty,
            "Reserved": c.reserved_qty,
            "Distributed": c.distributed_qty,
            "Stock Status": c.stock_status,
        } for c in sorted(catalog, key=lambda x: x.title)])

        st.dataframe(cat_df, width=True, hide_index=True)
    else:
        st.info("No books in catalog yet.")

    st.divider()

    # ==================== VISUAL BREAKDOWN ====================
    st.markdown("<div class='section-title'>📈 Distribution Breakdown</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        labels = ['Available', 'With Volunteers', 'With Teachers', 'Distributed']
        values = [available_total, len(copies_with_volunteers), len(copies_with_teachers), len(copies_distributed)]
        colors = ['#4caf50', '#ff9800', '#9c27b0', '#2196f3']

        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.55,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside'
        )])
        fig.update_layout(
            title="Book Status Distribution",
            showlegend=True,
            height=350,
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, width=True)

    with col2:
        class_counts = {}
        for c in catalog:
            class_counts[c.target_class] = class_counts.get(c.target_class, 0) + c.total_qty

        fig = go.Figure(data=[go.Bar(
            x=list(class_counts.keys()),
            y=list(class_counts.values()),
            marker_color=['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#f44336', '#795548']
        )])
        fig.update_layout(
            title="Total Books by Class",
            xaxis_title="Class",
            yaxis_title="Total Copies",
            height=350,
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, width=True)

    st.divider()

    # ==================== VOLUNTEER HOLDINGS ====================
    st.markdown("<div class='section-title'>👥 Who Has the Books?</div>", unsafe_allow_html=True)

    if volunteer_holdings or teacher_holdings:
        holdings_data = []

        for name, count in sorted(volunteer_holdings.items(), key=lambda x: x[1], reverse=True):
            holdings_data.append({"Name": name, "Type": "Volunteer", "Books Held": count})

        for name, count in sorted(teacher_holdings.items(), key=lambda x: x[1], reverse=True):
            holdings_data.append({"Name": name, "Type": "Teacher", "Books Held": count})

        holdings_df = pd.DataFrame(holdings_data)
        st.dataframe(holdings_df, width=True, hide_index=True)

        # Bar chart
        fig = go.Figure()
        vol_data = [(n, c) for n, c in volunteer_holdings.items()]
        teacher_data = [(n, c) for n, c in teacher_holdings.items()]

        if vol_data:
            fig.add_trace(go.Bar(
                x=[n for n, _ in vol_data],
                y=[c for _, c in vol_data],
                name='Volunteers',
                marker_color='#2d5a4a'
            ))
        if teacher_data:
            fig.add_trace(go.Bar(
                x=[n for n, _ in teacher_data],
                y=[c for _, c in teacher_data],
                name='Teachers',
                marker_color='#c9a227'
            ))

        fig.update_layout(
            title="Books Held by Each Person",
            xaxis_title="Name",
            yaxis_title="Books Held",
            barmode='group',
            height=350
        )
        st.plotly_chart(fig, width=True)
    else:
        st.info("No books currently assigned to volunteers or teachers.")

    st.divider()

    # ==================== KEY INSIGHTS ====================
    st.markdown("<div class='section-title'>💡 Key Insights</div>", unsafe_allow_html=True)

    distribution_rate = (len(copies_distributed) / total_books * 100) if total_books > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="insight-card">
            <h4 style="margin:0 0 8px 0; color:#1a3a2f;">📦 Books Yet to Reach Students</h4>
            <p style="margin:0; font-size:24px; font-weight:700; color:#ff9800;">{available_total + len(copies_with_volunteers) + len(copies_with_teachers)}</p>
            <p style="margin:4px 0 0 0; font-size:12px; color:#666;">
                {available_total} in stock + {len(copies_with_volunteers)} with volunteers + {len(copies_with_teachers)} with teachers
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="insight-card" style="border-left-color:#4caf50;">
            <h4 style="margin:0 0 8px 0; color:#1a3a2f;">✅ Distribution Progress</h4>
            <p style="margin:0; font-size:24px; font-weight:700; color:#4caf50;">{distribution_rate:.1f}%</p>
            <p style="margin:4px 0 0 0; font-size:12px; color:#666;">
                {len(copies_distributed)} of {total_books} books distributed to students
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(f"""
        <div class="insight-card" style="border-left-color:#2196f3;">
            <h4 style="margin:0 0 8px 0; color:#1a3a2f;">🚚 Pending Fulfillment</h4>
            <p style="margin:0; font-size:24px; font-weight:700; color:#2196f3;">{pending_requests}</p>
            <p style="margin:4px 0 0 0; font-size:12px; color:#666;">
                Books requested but not yet approved/fulfilled
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        low_stock = [c for c in catalog if c.available_qty <= 5 and c.available_qty > 0]
        out_of_stock = [c for c in catalog if c.available_qty == 0]
        st.markdown(f"""
        <div class="insight-card" style="border-left-color:#f44336;">
            <h4 style="margin:0 0 8px 0; color:#1a3a2f;">⚠️ Stock Alerts</h4>
            <p style="margin:0; font-size:24px; font-weight:700; color:#f44336;">{len(low_stock) + len(out_of_stock)}</p>
            <p style="margin:4px 0 0 0; font-size:12px; color:#666;">
                {len(low_stock)} low stock + {len(out_of_stock)} out of stock titles
            </p>
        </div>
        """, unsafe_allow_html=True)
