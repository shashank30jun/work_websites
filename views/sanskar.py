"""
Sanskar Operations View: Form Registration & AWGP / Shantikunj Analytics Dashboard
"""

from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import CONFIG
from models.sanskar_list import SanskarRecord
from utils.validators import sanitize_input, validate_phone


def _get_active_volunteers_safe(sheets_service):
    """Safely fetch active volunteers without throwing uncaught exceptions."""
    try:
        records = sheets_service.get_all_records(CONFIG.WORKSHEET_VOLUNTEERS)
        if not records:
            return []
        return [
            r.get("Name", "")
            for r in records
            if str(r.get("Is_Active", "")).lower() in ["yes", "true", "1"]
            and r.get("Name")
        ]
    except Exception:
        return []


def _categorize_sanskar(sanskar_name: str) -> str:
    """Categorizes Sanskar into AWGP 4 Life-Stage Buckets."""
    if not sanskar_name:
        return "💍 Grihastha & Social (गृहस्थ / सामाजिक)"
    s_lower = str(sanskar_name).lower()
    if any(k in s_lower for k in ["garbh", "punsavan", "simant", "pregnancy"]):
        return "🤰 Pre-natal (गर्भ-कालीन)"
    elif any(
        k in s_lower
        for k in ["namkaran", "naamkaran", "annapra", "mundan", "birthday", "janm"]
    ):
        return "👶 Childhood (बाल / शिशु)"
    elif any(
        k in s_lower
        for k in ["vidya", "yagyopaveet", "janeu", "deeksha", "diksha", "student"]
    ):
        return "🎓 Education / Youth (शिक्षा / दीक्षा)"
    else:
        return "💍 Grihastha & Social (गृहस्थ / सामाजिक)"


def render_sanskar_registration(sheets_service):
    """AWGP Sanskar Operations Hub: Form Registration & Consumable Analytics Dashboard."""

    # --------------------------------------------------------------------------
    # CUSTOM CSS: Typography & Spacing Fixes
    # --------------------------------------------------------------------------
    st.markdown(
        """
        <style>
        /* 1. Reduce text size of placeholders */
        input::placeholder, textarea::placeholder {
            font-size: 0.82rem !important;
            opacity: 0.7 !important;
        }
        
        /* 2. Reduce "Press Enter to submit form" hint size by 2px (14px -> 12px) */
        div[data-testid="stFormInstructions"], 
        small[data-testid="stFormInstructions"] {
            font-size: 11px !important;
            opacity: 0.65 !important;
        }
        
        /* Form Label Optimization */
        .stTextInput label, .stSelectbox label, .stNumberInput label {
            font-weight: 500 !important;
            font-size: 0.90rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_title, col_view = st.columns([2.5, 1.5])

    with col_view:
        view_mode = st.segmented_control(
            "View Mode",
            options=["📝 Register", "📊 Dashboard"],
            default="📝 Register",
            label_visibility="collapsed",
        )

    with col_title:
        st.header("🕉️ Sanskar Operations")
        st.caption(
            "Gayatri Pariwar • Shantikunj Cultural & Spiritual Event Management"
        )

    st.divider()

    # Safely fetch records
    sanskar_list = []
    try:
        raw_records = sheets_service.get_all_records(CONFIG.WORKSHEET_SANSKAR_LIST)
        if raw_records:
            sanskar_list = [
                SanskarRecord.from_row(r)
                for r in raw_records
                if isinstance(r, dict) and any(r.values())
            ]
    except Exception as e:
        st.warning(f"Note: Could not load existing Sanskar records: {str(e)}")

    # ==========================================================================
    # VIEW 1: SPACIOUS REGISTRATION FORM
    # ==========================================================================
    if view_mode == "📝 Register":
        active_vols = _get_active_volunteers_safe(sheets_service)
        vol_options = ["Auto-assign"] + active_vols

        with st.form("sanskar_registration_form", clear_on_submit=True):
            st.markdown("##### **1️⃣ Event Details (संस्कार विवरण)**")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                sanskar_name = st.text_input(
                    "Sanskar Name *",
                    placeholder="e.g., Punsavan, Namkaran",
                )
            with c2:
                occasion = st.text_input(
                    "Occasion *",
                    placeholder="Event context or reason",
                )

            st.write("")

            st.markdown("##### **2️⃣ Requester Details (आवेदक विवरण)**")
            c3, c4, c5 = st.columns(3, gap="medium")
            with c3:
                requester_name = st.text_input(
                    "Requester Name *",
                    placeholder="Full name of devotee/family",
                )
            with c4:
                requester_contact = st.text_input(
                    "Contact Number *",
                    placeholder="10-digit mobile number",
                )
            with c5:
                requester_type = st.selectbox(
                    "Requester Type",
                    ["Student", "Teacher", "Parent", "Volunteer / कार्यकर्ता", "Other"],
                )

            st.write("")

            st.markdown("##### **3️⃣ Coordination & Logistics (व्यवस्थापन)**")
            c6, c7 = st.columns(2, gap="large")
            with c6:
                no_of_people = st.number_input(
                    "Expected Attendance (जन सहभागिता)",
                    min_value=1,
                    value=10,
                    step=5,
                )
            with c7:
                assigned_volunteer = st.selectbox(
                    "Assigned Volunteer (कर्मठ कार्यकर्ता)", vol_options
                )

            notes = st.text_area(
                "Event Notes / Remarks",
                placeholder="Additional instructions or notes...",
                max_chars=300,
            )

            st.divider()

            _, btn_col = st.columns([3, 1])
            with btn_col:
                submitted = st.form_submit_button(
                    "Submit Sanskar Request 🕉️", type="primary", use_container_width=True
                )

            if submitted:
                errors = []
                if not sanskar_name or not sanskar_name.strip():
                    errors.append("Sanskar Name is required.")
                if not requester_name or not requester_name.strip():
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

    # ==========================================================================
    # VIEW 2: VECTORIZED ANALYTICS DASHBOARD
    # ==========================================================================
    else:
        st.subheader("📊 Shantikunj Sanskar Operations & Impact")

        if not sanskar_list:
            st.info("No Sanskar records registered yet. Switch to 'Register' mode above to log events!")
            return

        # Vectorized Pandas Dataframe for fast analytics
        df = pd.DataFrame([s.__dict__ for s in sanskar_list])
        df["Attendance"] = pd.to_numeric(df["no_of_people"], errors="coerce").fillna(0).astype(int)
        df["Category"] = df["sanskar_name"].apply(_categorize_sanskar)

        current_ym = datetime.now().strftime("%Y-%m")
        df["Is_This_Month"] = df["timestamp"].astype(str).str.startswith(current_ym)

        # Metrics Aggregation
        total_sanskars = len(df)
        this_month_sanskars = int(df["Is_This_Month"].sum())
        pending_sanskars = len(df[df["status"].str.lower() == "pending"])
        fulfilled_sanskars = len(df[df["status"].str.lower() == "fulfilled"])
        
        total_reach = int(df["Attendance"].sum())
        month_reach = int(df[df["Is_This_Month"]]["Attendance"].sum())
        
        active_vols = df[
            (df["assigned_volunteer"].str.strip() != "") & 
            (df["assigned_volunteer"] != "Auto-assign")
        ]["assigned_volunteer"].nunique()

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Sanskars", f"{total_sanskars:,}")
        m2.metric("This Month", f"{this_month_sanskars:,}", f"+{this_month_sanskars} new")
        m3.metric("Pending Request", f"{pending_sanskars:,}")
        m4.metric("Total Reach", f"{total_reach:,} ppl")
        m5.metric("Month Reach", f"{month_reach:,} ppl")
        m6.metric("Volunteers Active", f"{active_vols:,}")

        st.divider()

        tab_upcoming, tab_stage, tab_ops, tab_log = st.tabs(
            [
                "📅 Upcoming Sanskars",
                "🕉️ 16 Sanskar Life-Stage Impact",
                "🍩 Workflow & Volunteers",
                "📋 Master Register",
            ]
        )

        with tab_upcoming:
            st.markdown("##### **📅 Upcoming Scheduled & Pending Sanskars**")
            df_pending = df[df["status"].str.lower() == "pending"]

            if df_pending.empty:
                st.success("🎉 All scheduled Sanskars have been completed! No pending requests.")
            else:
                up_total = len(df_pending)
                up_reach = int(df_pending["Attendance"].sum())
                unassigned_count = len(df_pending[
                    (df_pending["assigned_volunteer"].str.strip() == "") | 
                    (df_pending["assigned_volunteer"] == "Auto-assign")
                ])

                c_u1, c_u2, c_u3 = st.columns(3)
                c_u1.metric("Upcoming Events", f"{up_total}")
                c_u2.metric("Expected Reach", f"{up_reach:,} attendees")
                c_u3.metric(
                    "Unassigned Events",
                    f"{unassigned_count}",
                    delta="Needs Coordinator" if unassigned_count > 0 else "All Assigned",
                )

                st.divider()

                df_display_up = df_pending.rename(columns={
                    "sanskar_name": "Sanskar Name",
                    "Category": "Type / Life-Stage",
                    "occasion": "Occasion / Context",
                    "requester_name": "Requester Name",
                    "requester_contact": "Contact",
                    "requester_type": "Requester Category",
                    "Attendance": "Expected Attendance",
                    "assigned_volunteer": "Assigned Volunteer",
                    "status": "Status",
                    "timestamp": "Requested On"
                })[[
                    "Sanskar Name", "Type / Life-Stage", "Occasion / Context", 
                    "Requester Name", "Contact", "Requester Category", 
                    "Expected Attendance", "Assigned Volunteer", "Status", "Requested On"
                ]]

                st.dataframe(
                    df_display_up,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Expected Attendance": st.column_config.NumberColumn(format="%d ppl"),
                    },
                )

        with tab_stage:
            col_l, col_r = st.columns(2)

            with col_l:
                st.markdown("##### **Events by Life-Stage Category**")
                stage_counts = df["Category"].value_counts().to_dict()
                
                # Standardized order guarantee
                all_stages = [
                    "🤰 Pre-natal (गर्भ-कालीन)",
                    "👶 Childhood (बाल / शिशु)",
                    "🎓 Education / Youth (शिक्षा / दीक्षा)",
                    "💍 Grihastha & Social (गृहस्थ / सामाजिक)"
                ]
                x_vals = [stage_counts.get(stg, 0) for stg in all_stages]

                fig_stage = go.Figure(
                    data=[
                        go.Bar(
                            y=all_stages,
                            x=x_vals,
                            orientation="h",
                            marker_color=["#EC4899", "#3B82F6", "#10B981", "#F59E0B"],
                            text=x_vals,
                            textposition="auto",
                        )
                    ]
                )
                fig_stage.update_layout(
                    xaxis_title="Number of Events",
                    height=320,
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig_stage, width="stretch")

            with col_r:
                st.markdown("##### **Popularity by Specific Sanskar Name**")
                name_counts = df["sanskar_name"].str.title().value_counts()

                fig_names = go.Figure(
                    data=[
                        go.Bar(
                            x=name_counts.index.tolist(),
                            y=name_counts.values.tolist(),
                            marker_color="#2d5a4a",
                            text=name_counts.values.tolist(),
                            textposition="auto",
                        )
                    ]
                )
                fig_names.update_layout(
                    xaxis_title="Sanskar Name",
                    yaxis_title="Count",
                    height=320,
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig_names, width="stretch")

        with tab_ops:
            col_ops1, col_ops2 = st.columns(2)

            with col_ops1:
                st.markdown("##### **Request Status Breakdown**")
                fig_status = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Pending", "Fulfilled"],
                            values=[pending_sanskars, fulfilled_sanskars],
                            hole=0.6,
                            marker_colors=["#F59E0B", "#10B981"],
                            textinfo="label+percent+value",
                        )
                    ]
                )
                fig_status.update_layout(
                    height=320,
                    showlegend=True,
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig_status, width="stretch")

            with col_ops2:
                st.markdown("##### **Volunteer Event Assignments**")
                vol_series = df["assigned_volunteer"].replace("", "Unassigned / Auto").value_counts()

                fig_vol = go.Figure(
                    data=[
                        go.Bar(
                            x=vol_series.index.tolist(),
                            y=vol_series.values.tolist(),
                            marker_color="#6366F1",
                            text=vol_series.values.tolist(),
                            textposition="auto",
                        )
                    ]
                )
                fig_vol.update_layout(
                    xaxis_title="Volunteer Name",
                    yaxis_title="Events Assigned",
                    height=320,
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig_vol, width="stretch")

        with tab_log:
            st.markdown("##### **📋 All Registered Sanskar Events (Historical Log)**")
            df_master = df.rename(columns={
                "sanskar_name": "Sanskar Name",
                "Category": "Category",
                "occasion": "Occasion",
                "requester_name": "Requester",
                "requester_contact": "Contact",
                "requester_type": "Type",
                "Attendance": "Attendance",
                "status": "Status",
                "assigned_volunteer": "Assigned Volunteer",
                "timestamp": "Timestamp"
            })[[
                "Sanskar Name", "Category", "Occasion", "Requester", 
                "Contact", "Type", "Attendance", "Status", 
                "Assigned Volunteer", "Timestamp"
            ]]
            df_master["Assigned Volunteer"] = df_master["Assigned Volunteer"].replace("", "Unassigned")

            st.dataframe(df_master, width="stretch", hide_index=True)
