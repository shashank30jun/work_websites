"""
Sanskar Operations View: Form Registration & AWGP / Shantikunj Analytics Dashboard
Optimized Modular Architecture with Generic Sequential ID Tracking (SNKQR_0001_DDMMYYYY)
"""

from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import CONFIG
from models.sanskar_list import SanskarRecord
from utils.formatters import generate_sequential_id
from utils.validators import sanitize_input, validate_pincode, validate_phone

FORM_CSS = """
<style>
input::placeholder, textarea::placeholder { font-size: 0.82rem !important; opacity: 0.6 !important; color: #6b7280 !important; }
div[data-testid="stFormInstructions"], small[data-testid="stFormInstructions"], span[data-testid="stFormInstructions"] { display: none !important; }
.stTextInput label, .stSelectbox label, .stNumberInput label, .stDateInput label { font-weight: 500 !important; font-size: 0.90rem !important; }
</style>
"""


# ==============================================================================
# 1. HELPERS & UTILITIES
# ==============================================================================

def _get_active_volunteers(sheets_service) -> list:
    try:
        records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS) or []
        return [
            r.get("Name", "")
            for r in records
            if str(r.get("Is_Active", "")).lower() in ["yes", "true", "1"] and r.get("Name")
        ]
    except Exception:
        return []


def _categorize_sanskar(sanskar_name: str) -> str:
    s = str(sanskar_name or "").lower()
    if any(k in s for k in ["garbh", "punsavan", "simant", "pregnancy"]):
        return "🤰 Pre-natal (गर्भ-कालीन)"
    if any(k in s for k in ["namkaran", "naamkaran", "annapra", "mundan", "birthday", "janm"]):
        return "👶 Childhood (बाल / शिशु)"
    if any(k in s for k in ["vidya", "yagyopaveet", "janeu", "deeksha", "diksha", "student"]):
        return "🎓 Education / Youth (शिक्षा / दीक्षा)"
    return "💍 Grihastha & Social (गृहस्थ / सामाजिक)"


def _create_bar_chart(x, y, orientation="v", colors=None, x_title="", y_title=""):
    fig = go.Figure(
        go.Bar(
            x=x, y=y, orientation=orientation, text=x if orientation == "h" else y,
            textposition="auto", marker_color=colors or "#3B82F6"
        )
    )
    fig.update_layout(
        height=320, xaxis_title=x_title, yaxis_title=y_title,
        margin=dict(t=10, b=10, l=10, r=10)
    )
    return fig


# ==============================================================================
# 2. SUB-VIEW 1: FORM REGISTRATION
# ==============================================================================

def _render_registration_form(sheets_service, sanskar_list: list):
    vol_options = ["Auto-assign"] + _get_active_volunteers(sheets_service)

    # Generate sequential ID using SNKQR prefix
    generated_req_id = generate_sequential_id("SNKQR", sanskar_list, id_attribute="req_id")
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with st.form("sanskar_form", clear_on_submit=True):
        st.markdown("##### **1️⃣ System Auto-Fields & Sanskar Date**")
        c_meta1, c_meta2, c_meta3 = st.columns([2, 2, 2], gap="medium")
        c_meta1.text_input("Request ID (Auto)", value=generated_req_id, disabled=True)
        c_meta2.text_input("Created Timestamp", value=current_time_str, disabled=True)
        sanskar_date = c_meta3.date_input("Date of Sanskar (संस्कार तिथि) *", datetime.now())

        sanskar_name = st.text_input("Sanskar Name *", placeholder="e.g., Punsavan, Namkaran, Vidyarambha")

        st.markdown("##### **2️⃣ Devotee & Family Details (आवेदक एवं अभिभावक)**")
        c3, c4, c5, c6 = st.columns([2, 1, 2, 2], gap="small")
        requester_name = c3.text_input("Devotee Full Name *", placeholder="Name of devotee/family")
        relation_type = c4.selectbox("Relation", ["S/O", "D/O", "W/O", "H/O", "C/O"])
        guardian_name = c5.text_input("Father / Guardian Name", placeholder="Relative or Parent Name")
        requester_contact = c6.text_input("Contact Number *", placeholder="10-digit mobile number")

        c7, c8, c9 = st.columns([3, 1.5, 2], gap="small")
        address = c7.text_input("Address (स्थान / पता)", placeholder="Complete event address")
        pin_code = c8.text_input("Pin Code *", placeholder="6-digit PIN", max_chars=6)
        requester_type = c9.selectbox("Requester Category", ["Student", "Teacher", "Parent", "Volunteer / कार्यकर्ता", "Other"])

        st.markdown("##### **3️⃣ Coordination & Logistics (व्यवस्थापन)**")
        ca, cb = st.columns(2, gap="large")
        no_of_people = ca.number_input("Expected Attendance (जन सहभागिता)", min_value=1, value=10, step=5)
        assigned_volunteer = cb.selectbox("Assigned Volunteer (कर्मठ कार्यकर्ता)", vol_options)
        notes = st.text_area("Event Notes / Remarks", placeholder="Special arrangements or notes...", max_chars=300)

        st.divider()
        _, btn_col = st.columns([3, 1])
        submitted = btn_col.form_submit_button("Submit Request", type="primary", use_container_width=True)

    if submitted:
        errors = []
        if not sanskar_name or not sanskar_name.strip():
            errors.append("Sanskar Name is required.")
        if not requester_name or not requester_name.strip():
            errors.append("Requester Name is required.")

        valid_phone, phone_res = validate_phone(requester_contact)
        if not valid_phone:
            errors.append(phone_res)

        valid_pin, pin_res = validate_pincode(pin_code)
        if not valid_pin:
            errors.append(pin_res)

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            record = SanskarRecord(
                req_id=generated_req_id,
                sanskar_name=sanitize_input(sanskar_name),
                sanskar_date=str(sanskar_date),
                created_timestamp=current_time_str,
                requester_name=sanitize_input(requester_name),
                relation_type=relation_type,
                guardian_name=sanitize_input(guardian_name),
                requester_contact=phone_res,
                requester_type=requester_type,
                address=sanitize_input(address),
                pin_code=pin_res,
                no_of_people=str(no_of_people),
                status="Pending",
                assigned_volunteer=(assigned_volunteer if assigned_volunteer != "Auto-assign" else ""),
                notes=sanitize_input(notes),
            )
            try:
                sheets_service.append_row(CONFIG.WORKSHEET_SANSKAR_LIST, record.to_row())
                st.success(f"✅ Sanskar event registered successfully! Request ID: **{generated_req_id}**")
            except Exception as e:
                st.error(f"Failed to submit: {str(e)}")


# ==============================================================================
# 3. SUB-VIEW 2: ANALYTICS DASHBOARD
# ==============================================================================

def _render_dashboard(sanskar_list):
    st.subheader("📊 Shantikunj Sanskar Operations & Impact")
    if not sanskar_list:
        st.info("No Sanskar records registered yet. Switch to 'Register' mode above to log events!")
        return

    df = pd.DataFrame([s.__dict__ for s in sanskar_list])
    df["Attendance"] = pd.to_numeric(df["no_of_people"], errors="coerce").fillna(0).astype(int)
    df["Category"] = df["sanskar_name"].apply(_categorize_sanskar)
    df["Is_This_Month"] = df["created_timestamp"].astype(str).str.startswith(datetime.now().strftime("%Y-%m"))

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Sanskars", f"{len(df):,}")
    m2.metric("This Month", f"{df['Is_This_Month'].sum():,}", f"+{df['Is_This_Month'].sum()} new")
    m3.metric("Pending Request", f"{(df['status'].str.lower() == 'pending').sum():,}")
    m4.metric("Total Reach", f"{df['Attendance'].sum():,} ppl")
    m5.metric("Month Reach", f"{df[df['Is_This_Month']]['Attendance'].sum():,} ppl")
    m6.metric(
        "Volunteers Active",
        f"{df[(df['assigned_volunteer'].str.strip() != '') & (df['assigned_volunteer'] != 'Auto-assign')]['assigned_volunteer'].nunique():,}",
    )

    st.divider()
    t_upcoming, t_stage, t_ops, t_log = st.tabs(
        ["📅 Upcoming Sanskars", "🕉️ 16 Sanskar Life-Stage Impact", "🍩 Workflow & Volunteers", "📋 Master Register"]
    )

    with t_upcoming:
        df_up = df[df["status"].str.lower() == "pending"]
        if df_up.empty:
            st.success("🎉 All scheduled Sanskars have been completed! No pending requests.")
        else:
            unassigned = len(
                df_up[
                    (df_up["assigned_volunteer"].str.strip() == "")
                    | (df_up["assigned_volunteer"] == "Auto-assign")
                ]
            )
            u1, u2, u3 = st.columns(3)
            u1.metric("Upcoming Events", f"{len(df_up)}")
            u2.metric("Expected Reach", f"{df_up['Attendance'].sum():,} attendees")
            u3.metric("Unassigned Events", f"{unassigned}", delta="Needs Coordinator" if unassigned > 0 else "All Assigned")
            st.divider()

            cols_map = {
                "req_id": "Request ID",
                "sanskar_name": "Sanskar Name",
                "sanskar_date": "Sanskar Date",
                "Category": "Type / Life-Stage",
                "requester_name": "Requester",
                "guardian_name": "Guardian / Parent",
                "requester_contact": "Contact",
                "address": "Address",
                "pin_code": "Pin Code",
                "Attendance": "Expected Attendance",
                "assigned_volunteer": "Assigned Volunteer",
                "status": "Status",
            }
            st.dataframe(df_up.rename(columns=cols_map)[list(cols_map.values())], width="stretch", hide_index=True)

    with t_stage:
        c_l, c_r = st.columns(2)
        stages = [
            "🤰 Pre-natal (गर्भ-कालीन)",
            "👶 Childhood (बाल / शिशु)",
            "🎓 Education / Youth (शिक्षा / दीक्षा)",
            "💍 Grihastha & Social (गृहस्थ / सामाजिक)",
        ]
        counts = df["Category"].value_counts().to_dict()

        c_l.markdown("##### **Events by Life-Stage Category**")
        c_l.plotly_chart(
            _create_bar_chart(
                y=stages, x=[counts.get(s, 0) for s in stages], orientation="h",
                colors=["#EC4899", "#3B82F6", "#10B981", "#F59E0B"], x_title="Number of Events"
            ),
            width="stretch",
        )

        c_r.markdown("##### **Popularity by Specific Sanskar Name**")
        nc = df["sanskar_name"].str.title().value_counts()
        c_r.plotly_chart(
            _create_bar_chart(x=nc.index.tolist(), y=nc.values.tolist(), colors="#2d5a4a", x_title="Sanskar Name", y_title="Count"),
            width="stretch",
        )

    with t_ops:
        c_o1, c_o2 = st.columns(2)
        c_o1.markdown("##### **Request Status Breakdown**")
        fig_pie = go.Figure(
            go.Pie(
                labels=["Pending", "Fulfilled"],
                values=[(df["status"].str.lower() == "pending").sum(), (df["status"].str.lower() == "fulfilled").sum()],
                hole=0.6, marker_colors=["#F59E0B", "#10B981"], textinfo="label+percent+value"
            )
        )
        fig_pie.update_layout(height=320, showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
        c_o1.plotly_chart(fig_pie, width="stretch")

        c_o2.markdown("##### **Volunteer Event Assignments**")
        vc = df["assigned_volunteer"].replace("", "Unassigned / Auto").value_counts()
        c_o2.plotly_chart(
            _create_bar_chart(x=vc.index.tolist(), y=vc.values.tolist(), colors="#6366F1", x_title="Volunteer Name", y_title="Events Assigned"),
            width="stretch",
        )

    with t_log:
        st.markdown("##### **📋 All Registered Sanskar Events (Master Historical Register)**")
        log_map = {
            "req_id": "Request ID",
            "sanskar_name": "Sanskar Name",
            "sanskar_date": "Sanskar Date",
            "Category": "Category",
            "requester_name": "Requester",
            "relation_type": "Relation",
            "guardian_name": "Guardian/Parent",
            "requester_contact": "Contact",
            "address": "Address",
            "pin_code": "Pin Code",
            "Attendance": "Attendance",
            "status": "Status",
            "assigned_volunteer": "Assigned Volunteer",
            "created_timestamp": "Submitted Timestamp",
        }
        df_log = df.rename(columns=log_map)[list(log_map.values())]
        df_log["Assigned Volunteer"] = df_log["Assigned Volunteer"].replace("", "Unassigned")
        st.dataframe(df_log, width="stretch", hide_index=True)


# ==============================================================================
# 4. MAIN ENTRY POINT
# ==============================================================================

def render_sanskar_registration(sheets_service):
    st.markdown(FORM_CSS, unsafe_allow_html=True)

    col_title, col_view = st.columns([2.5, 1.5])
    view_mode = col_view.segmented_control("View Mode", options=["📝 Register", "📊 Dashboard"], default="📝 Register", label_visibility="collapsed")
    col_title.header("🕉️ Sanskar Operations")
    col_title.caption("Gayatri Pariwar • Shantikunj Cultural & Spiritual Event Management")
    st.divider()

    sanskar_list = []
    try:
        raw_records = sheets_service.get_all_records(CONFIG.WORKSHEET_SANSKAR_LIST) or []
        sanskar_list = [SanskarRecord.from_row(r) for r in raw_records if isinstance(r, dict) and any(r.values())]
    except Exception as e:
        st.warning(f"Note: Could not load existing Sanskar records: {str(e)}")

    if view_mode == "📝 Register":
        _render_registration_form(sheets_service, sanskar_list)
    else:
        _render_dashboard(sanskar_list)
