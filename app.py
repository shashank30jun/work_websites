
"""
BSGP Book Redistribution Platform
Clean rewrite: Native Streamlit components, no custom HTML/CSS
"""

import os
import streamlit as st
from dotenv import load_dotenv

from config import (
    CONFIG, MASTER_CATALOG_HEADERS, STOCK_LEDGER_HEADERS,
    REQUESTS_HEADERS, DISTRIBUTION_HEADERS, VOLUNTEERS_HEADERS
)
from services.sheets_service import GoogleSheetsService

load_dotenv()

st.set_page_config(
    page_title=CONFIG.APP_TITLE,
    page_icon=CONFIG.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_sheets_service():
    return GoogleSheetsService(
        credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        sheet_name=CONFIG.SHEET_NAME
    )


def init_sheets(sheets_service):
    try:
        sheets_service.ensure_headers(CONFIG.WORKSHEET_MASTER_CATALOG, MASTER_CATALOG_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_STOCK_LEDGER, STOCK_LEDGER_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_REQUESTS, REQUESTS_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_DISTRIBUTION, DISTRIBUTION_HEADERS)
        sheets_service.ensure_headers(CONFIG.WORKSHEET_VOLUNTEERS, VOLUNTEERS_HEADERS)
    except Exception as e:
        st.error(f"Failed to initialize sheets: {str(e)}")


def render_header():
    """Clean native Streamlit header."""
    st.title(f"{CONFIG.APP_ICON} {CONFIG.APP_TITLE}")
    st.caption(CONFIG.APP_SUBTITLE)
    st.divider()


def render_sidebar():
    with st.sidebar:
        st.header("🕉️ BSGP Platform")
        st.caption("DSVV • Shantikunj")
        st.divider()

        page = st.radio(
            "Navigate",
            [
                "🏠 Home Dashboard",
                "📖 Book Catalog",
                "📝 Request a Book",
                "📊 Admin Dashboard",
                "ℹ️ About BSGP"
            ],
            label_visibility="collapsed"
        )

        st.divider()
        st.info("**Quick Info**\n\n• Classes: 5 to 10\n• Exam: BSGP\n• Org: DSVV, Haridwar")
        st.divider()
        st.caption("© 2024 DSVV")

        return page


def render_home_dashboard(sheets_service):
    """Home Dashboard using ONLY native Streamlit components."""
    import pandas as pd
    import plotly.graph_objects as go
    from models.master_catalog import MasterCatalogItem
    from models.stock_ledger import StockLedgerItem
    from utils.formatters import format_currency

    st.header("📊 Dashboard Overview")

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

    # Calculate metrics
    total_books = sum(c.total_qty for c in catalog)
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog)
    available_total = sum(c.available_qty for c in catalog)
    reserved_total = sum(c.reserved_qty for c in catalog)
    distributed_total = sum(c.distributed_qty for c in catalog)

    copies_with_volunteers = len([l for l in ledger if l.is_with_volunteer])
    copies_with_teachers = len([l for l in ledger if l.status == "In_Transit" and l.holder_type == "Teacher"])
    copies_distributed = len([l for l in ledger if l.is_distributed])

    schools = set()
    students_registered = 0
    for r in req_records:
        if r.get("School_Name"):
            schools.add(r.get("School_Name"))
        if r.get("Requester_Type") == "Student":
            students_registered += int(r.get("Qty_Requested", 0) or 0)

    pending_requests = sum(int(r.get("Qty_Requested", 0) or 0) for r in req_records if r.get("Request_Status") == "Pending")

    # Metric cards using native st.metric
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Books", f"{total_books:,}", f"{format_currency(total_cost)} value")
    col2.metric("Available", f"{available_total:,}", "In stock")
    col3.metric("In Transit", f"{copies_with_volunteers + copies_with_teachers:,}", "With volunteers & teachers")
    col4.metric("Distributed", f"{copies_distributed:,}", "To students")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Schools", f"{len(schools)}")
    col6.metric("Students", f"{students_registered}")
    col7.metric("With Teachers", f"{copies_with_teachers}")
    col8.metric("With Volunteers", f"{copies_with_volunteers}")

    st.divider()

    # Books Inventory by Title
    st.subheader("📚 Books Inventory by Title")
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
            "Status": c.stock_status,
        } for c in sorted(catalog, key=lambda x: x.title)])
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    st.divider()

    # Charts
    st.subheader("📈 Distribution Breakdown")
    c1, c2 = st.columns(2)

    with c1:
        labels = ['Available', 'With Volunteers', 'With Teachers', 'Distributed']
        values = [available_total, copies_with_volunteers, copies_with_teachers, copies_distributed]
        colors = ['#4caf50', '#ff9800', '#9c27b0', '#2196f3']

        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.55,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside'
        )])
        fig.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        class_counts = {}
        for c in catalog:
            class_counts[c.target_class] = class_counts.get(c.target_class, 0) + c.total_qty

        fig = go.Figure(data=[go.Bar(
            x=list(class_counts.keys()),
            y=list(class_counts.values()),
            marker_color=['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#f44336', '#795548']
        )])
        fig.update_layout(
            xaxis_title="Class",
            yaxis_title="Total Copies",
            height=350,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Volunteer Holdings
    st.subheader("👥 Who Has the Books?")

    volunteer_holdings = {}
    teacher_holdings = {}
    for item in ledger:
        if item.status == "In_Transit":
            if item.holder_type == "Volunteer":
                volunteer_holdings[item.current_holder] = volunteer_holdings.get(item.current_holder, 0) + 1
            elif item.holder_type == "Teacher":
                teacher_holdings[item.current_holder] = teacher_holdings.get(item.current_holder, 0) + 1

    if volunteer_holdings or teacher_holdings:
        holdings_data = []
        for name, count in sorted(volunteer_holdings.items(), key=lambda x: x[1], reverse=True):
            holdings_data.append({"Name": name, "Type": "Volunteer", "Books Held": count})
        for name, count in sorted(teacher_holdings.items(), key=lambda x: x[1], reverse=True):
            holdings_data.append({"Name": name, "Type": "Teacher", "Books Held": count})

        holdings_df = pd.DataFrame(holdings_data)
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)

        # Bar chart
        fig = go.Figure()
        if volunteer_holdings:
            fig.add_trace(go.Bar(
                x=list(volunteer_holdings.keys()),
                y=list(volunteer_holdings.values()),
                name='Volunteers',
                marker_color='#2d5a4a'
            ))
        if teacher_holdings:
            fig.add_trace(go.Bar(
                x=list(teacher_holdings.keys()),
                y=list(teacher_holdings.values()),
                name='Teachers',
                marker_color='#c9a227'
            ))

        fig.update_layout(
            xaxis_title="Name",
            yaxis_title="Books Held",
            barmode='group',
            height=350,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No books currently assigned to volunteers or teachers.")

    st.divider()

    # Key Insights
    st.subheader("💡 Key Insights")

    distribution_rate = (copies_distributed / total_books * 100) if total_books > 0 else 0
    low_stock = [c for c in catalog if c.available_qty <= 5 and c.available_qty > 0]
    out_of_stock = [c for c in catalog if c.available_qty == 0]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("📦 Books Yet to Reach Students", 
                  f"{available_total + copies_with_volunteers + copies_with_teachers}",
                  f"{available_total} stock + {copies_with_volunteers + copies_with_teachers} in transit")
    with c2:
        st.metric("✅ Distribution Progress", 
                  f"{distribution_rate:.1f}%",
                  f"{copies_distributed} of {total_books} books")

    c3, c4 = st.columns(2)
    with c3:
        st.metric("🚚 Pending Fulfillment", f"{pending_requests}")
    with c4:
        st.metric("⚠️ Stock Alerts", f"{len(low_stock) + len(out_of_stock)}", 
                  f"{len(low_stock)} low + {len(out_of_stock)} out of stock")


def render_catalog(sheets_service):
    """Book Catalog using native Streamlit."""
    from models.master_catalog import MasterCatalogItem
    from utils.formatters import get_status_badge, get_class_badge

    st.header("📖 Book Catalog")

    with st.spinner("Loading catalog..."):
        try:
            records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG)
            catalog = [MasterCatalogItem.from_row(r) for r in records]
        except Exception as e:
            st.error(f"Failed to load catalog: {str(e)}")
            return

    col1, col2, col3, col4 = st.columns([2, 1, 1, 0.8])

    with col1:
        search = st.text_input("🔍 Search", placeholder="Title, Author, or Genre...")
    with col2:
        class_filter = st.selectbox("Class", ["All"] + CONFIG.CLASSES)
    with col3:
        status_filter = st.selectbox("Stock Status", ["All", "In Stock", "Low Stock", "Out of Stock"])
    with col4:
        st.write("")
        st.write("")
        refresh = st.button("🔄 Refresh")

    if refresh:
        st.cache_data.clear()
        st.rerun()

    filtered = catalog
    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if (
            search_lower in c.title.lower() or 
            search_lower in c.author.lower() or 
            search_lower in c.genre.lower()
        )]

    if class_filter != "All":
        filtered = [c for c in filtered if c.target_class == class_filter]

    if status_filter != "All":
        filtered = [c for c in filtered if c.stock_status == status_filter]
    else:
        filtered = [c for c in filtered if c.is_in_stock]

    total_copies = sum(c.available_qty for c in filtered)
    st.caption(f"Showing {len(filtered)} titles ({total_copies} copies available)")

    if not filtered:
        st.info("No books found matching your criteria.")
        return

    # Display books in a clean grid using st.columns
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
                    st.write(f"{item.genre} • {item.language}")

                    c1, c2 = st.columns(2)
                    c1.write(f"📚 {item.target_class}")
                    if item.available_qty == 0:
                        c2.error("Out of Stock")
                    elif item.available_qty <= 5:
                        c2.warning(f"Only {item.available_qty} left")
                    else:
                        c2.success(f"{item.available_qty} available")

                    st.write(f"**{item.formatted_cost}** per copy | Total: {item.total_qty} copies")

                    if item.is_in_stock:
                        if st.button("Request Book", key=f"req_{item.catalog_id}", type="primary"):
                            st.session_state.selected_book = item
                            st.session_state.show_request_form = True
                            st.session_state.request_submitted = False
                            st.session_state.form_data = {}
                            st.rerun()
                    else:
                        st.button("Out of Stock", key=f"out_{item.catalog_id}", disabled=True)


def render_request_form(sheets_service):
    """Request form using native Streamlit."""
    from models.master_catalog import MasterCatalogItem
    from utils.validators import validate_phone, sanitize_input
    from datetime import datetime

    item = st.session_state.get("selected_book")

    if not item:
        st.info("Please select a book from the catalog first.")
        return

    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    st.header(f"📖 Request Book: {item.title}")
    st.caption(f"{item.target_class} | {item.available_qty} copies available out of {item.total_qty} total")

    if st.session_state.get("request_submitted", False):
        st.success(f"✅ Request submitted! Your Request ID: {st.session_state.get('last_request_id', '')}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 Submit Another Request", type="primary"):
                st.session_state.request_submitted = False
                st.session_state.form_data = {}
                st.session_state.last_request_id = ""
                st.rerun()
        with c2:
            if st.button("📖 Back to Catalog"):
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

        submitted = st.form_submit_button("Submit Request", type="primary")

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


def _update_catalog_qty(sheets_service, catalog_id, qty):
    """Update Master Catalog quantities when a request is made."""
    records = sheets_service.get_all_records(CONFIG.WORKSHEET_MASTER_CATALOG, use_cache=False)
    for idx, record in enumerate(records, start=2):
        if str(record.get("Catalog_ID", "")) == catalog_id:
            available = int(record.get("Available_Qty", 0) or 0)
            reserved = int(record.get("Reserved_Qty", 0) or 0)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 9, available - qty)
            sheets_service.update_cell(CONFIG.WORKSHEET_MASTER_CATALOG, idx, 11, reserved + qty)
            break


def render_admin_dashboard(sheets_service):
    """Admin Dashboard using native Streamlit."""
    import pandas as pd
    import plotly.graph_objects as go
    from models.master_catalog import MasterCatalogItem
    from models.stock_ledger import StockLedgerItem
    from utils.formatters import format_currency

    if not st.session_state.get("admin_authenticated", False):
        with st.form("admin_login"):
            st.subheader("🔐 Admin Login")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if password == st.secrets.get("ADMIN_PASSWORD", "bsgp2024"):
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    st.header("📊 Admin Dashboard")

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

    total_books = sum(c.total_qty for c in catalog)
    total_cost = sum(c.total_qty * c.cost_per_unit for c in catalog)
    available = sum(c.available_qty for c in catalog)
    reserved = sum(c.reserved_qty for c in catalog)
    distributed = sum(c.distributed_qty for c in catalog)
    pending_reqs = sum(int(r.get("Qty_Requested", 0) or 0) for r in req_records if r.get("Request_Status") == "Pending")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Books", f"{total_books}")
    c2.metric("Total Cost", format_currency(total_cost))
    c3.metric("Available", f"{available}")
    c4.metric("Reserved", f"{reserved}")
    c5.metric("Pending Qty", f"{pending_reqs}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribution by Class")
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
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Status Distribution")
        fig = go.Figure(data=[go.Bar(
            x=["Available", "Reserved", "Distributed"],
            y=[available, reserved, distributed],
            marker_color=['#4caf50', '#ff9800', '#2196f3']
        )])
        fig.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📋 Master Catalog")
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
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("📦 Stock Ledger")
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
            st.dataframe(led_df, use_container_width=True, hide_index=True)
        else:
            st.info("No individual copy records yet.")

    st.divider()

    st.subheader("📨 Pending Requests")
    pending = [r for r in req_records if r.get("Request_Status") == "Pending"]
    if pending:
        for req in pending:
            with st.container():
                cols = st.columns([3, 2, 2, 1, 1, 1])
                cols[0].write(f"**{req.get('Book_Title', '')}**")
                cols[1].write(f"{req.get('Requester_Name', '')}")
                cols[2].write(f"{req.get('School_Name', '')}")
                cols[3].write(f"Qty: {req.get('Qty_Requested', 0)}")

                if cols[4].button("✅ Approve", key=f"app_{req.get('Request_ID', '')}"):
                    _approve_request(sheets_service, req)
                    st.rerun()

                if cols[5].button("❌ Reject", key=f"rej_{req.get('Request_ID', '')}"):
                    _reject_request(sheets_service, req)
                    st.rerun()
    else:
        st.info("No pending requests.")

    st.divider()

    st.subheader("👥 Volunteer Activity")
    vol_df = pd.DataFrame([{
        "Name": v.get("Name", ""),
        "Type": v.get("Type", ""),
        "City": v.get("City", ""),
        "Holding": int(v.get("Books_Holding", 0) or 0),
        "Distributed Lifetime": int(v.get("Books_Distributed_Lifetime", 0) or 0),
        "Active": "Yes" if str(v.get("Is_Active", "")).lower() == "yes" else "No"
    } for v in vol_records])
    st.dataframe(vol_df, use_container_width=True, hide_index=True)

    st.subheader("💰 Cost Breakdown")
    cost_by_class = {}
    for c in catalog:
        cost_by_class[c.target_class] = cost_by_class.get(c.target_class, 0) + (c.total_qty * c.cost_per_unit)

    fig = go.Figure(data=[go.Bar(
        x=list(cost_by_class.keys()),
        y=list(cost_by_class.values()),
        marker_color='#2d5a4a'
    )])
    fig.update_layout(height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


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


def render_about():
    st.header("🕉️ About BSGP")

    st.write("""
    **Bharatiya Sanskriti Gyaan Pariksha (BSGP)** is a unique initiative by 
    **Dev Sanskriti Vishwavidyalaya (DSVV)**, Shantikunj, Haridwar.

    ### Purpose
    BSGP is conducted for students of **Classes 5 to 10** to:
    - Awaken cultural values and patriotism
    - Build character, confidence, and self-awareness
    - Connect the young generation with India's glorious heritage

    ### This Platform
    - **📚 Master Catalog** — Unique titles with quantities
    - **📦 Stock Ledger** — Individual copy tracking
    - **🔄 Distribution Log** — Every handover recorded
    - **👥 Volunteer coordination**

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
        ("admin_authenticated", False),
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
                if st.button("← Back to Catalog"):
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
