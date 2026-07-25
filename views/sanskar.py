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

    col_title, col_view = st.columns([3, 1])

    with col_view:
        view_mode = st.segmented_control(
            "View Mode",
            options=["📝 Register", "📊 Dashboard"],
            default="📝 Register",
            label_visibility="collapsed",
        )

    with col_title:
        st.header("🕉️ Sanskar Operations (16 संस्कार व्यवस्था)")
        st.caption(
            "Gayatri Pariwar • Shantikunj Cultural & Spiritual Event Management"
        )

    st.divider()

    # Safely fetch Sanskar records
    sanskar_list = []
    try:
        raw_records = sheets_service.get_all_records(
            CONFIG.WORKSHEET_SANSKAR_LIST
        )
        if raw_records:
            for r in raw_records:
                if isinstance(r, dict) and any(r.values()):
                    try:
                        sanskar_list.append(SanskarRecord.from_row(r))
                    except Exception:
                        continue
    except Exception as e:
        st.warning(f"Note: Could not load existing Sanskar records: {str(e)}")

    # ==========================================================================
    # VIEW 1: REGISTRATION FORM
    # ==========================================================================
    if view_mode == "📝 Register":
        active_vols = _get_active_volunteers_safe(sheets_service)
        vol_options = ["Auto-assign"] + active_vols

        with st.form("sanskar_registration_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                sanskar_name = st.text_input(
                    "Sanskar Name *",
                    placeholder="e.g., Punsavan, Namkaran, Vidyarambha, Birthday",
                )
                occasion = st.text_input(
                    "Occasion *", placeholder="Reason or context of event"
                )
                requester_name = st.text_input(
                    "Requester Name *", placeholder="Full name of devotee/family"
                )

            with col2:
                requester_contact = st.text_input(
                    "Contact Number *", placeholder="10-digit mobile number"
                )
                requester_type = st.selectbox(
                    "Requester Type",
                    [
                        "Student",
                        "Teacher",
                        "Parent",
                        "Volunteer / कार्यकर्ता",
                        "Other",
                    ],
                )
                no_of_people = st.number_input(
                    "Expected Attendance (जन सहभागिता)", min_value=1, value=10
                )

            assigned_volunteer = st.selectbox(
                "Assigned Volunteer (कर्मठ कार्यकर्ता)", vol_options
            )
            notes = st.text_area("Event Notes / Remarks", max_chars=300)

            submitted = st.form_submit_button("Submit Sanskar Request", type="primary")

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
    # VIEW 2: AWGP / SHANTIKUNJ SANSKAR DASHBOARD
    # ==========================================================================
    else:
        st.subheader("📊 Shantikunj Sanskar Operations & Impact")

        if not sanskar_list:
            st.info("No Sanskar records registered yet. Switch to 'Register' mode above to log events!")
            return

        current_ym = datetime.now().strftime("%Y-%m")
        
        total_sanskars = len(sanskar_list)
        this_month_sanskars = 0
        this_month_attendees = 0

        total_attendees = 0
        pending_sanskars = 0
        fulfilled_sanskars = 0

        assigned_vols = set()

        for s in sanskar_list:
            att = int(s.no_of_people) if str(s.no_of_people).isdigit() else 0
            total_attendees += att

            if s.is_pending:
                pending_sanskars += 1
            if s.is_fulfilled:
                fulfilled_sanskars += 1

            if s.timestamp and str(s.timestamp).startswith(current_ym):
                this_month_sanskars += 1
                this_month_attendees += att

            if s.assigned_volunteer and s.assigned_volunteer != "Auto-assign":
                assigned_vols.add(s.assigned_volunteer)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Sanskars", f"{total_sanskars:,}")
        m2.metric("This Month", f"{this_month_sanskars:,}", f"+{this_month_sanskars} new")
        m3.metric("Pending Request", f"{pending_sanskars:,}")
        m4.metric("Total Reach", f"{total_attendees:,} ppl")
        m5.metric("Month Reach", f"{this_month_attendees:,} ppl")
        m6.metric("Volunteers Active", f"{len(assigned_vols):,}")

        st.divider()

        tab_upcoming, tab_stage, tab_ops, tab_log = st.tabs([
            "📅 Upcoming Sanskars",
            "🕉️ 16 Sanskar Life-Stage Impact",
            "🍩 Workflow & Volunteers",
            "📋 Master Register"
        ])

        with tab_upcoming:
            st.markdown("##### **📅 Upcoming Scheduled & Pending Sanskars**")
            
            upcoming_events = [s for s in sanskar_list if s.is_pending]

            if not upcoming_events:
                st.success("🎉 All scheduled Sanskars have been completed! No pending requests.")
            else:
                up_total = len(upcoming_events)
                up_reach = sum(int(s.no_of_people) if str(s.no_of_people).isdigit() else 0 for s in upcoming_events)
                unassigned_count = len([s for s in upcoming_events if not s.assigned_volunteer or s.assigned_volunteer == "Auto-assign"])

                c_u1, c_u2, c_u3 = st.columns(3)
                c_u1.metric("Upcoming Events", f"{up_total}")
                c_u2.metric("Expected Reach", f"{up_reach:,} attendees")
                c_u3.metric("Unassigned Events", f"{unassigned_count}", delta="Needs Coordinator" if unassigned_count > 0 else "All Assigned")

                st.divider()

                df_upcoming = pd.DataFrame(
                    [
                        {
                            "Sanskar Name": str(s.sanskar_name).title(),
                            "Type / Life-Stage": _categorize_sanskar(s.sanskar_name),
                            "Occasion / Context": s.occasion,
                            "Requester Name": s.requester_name,
                            "Contact": s.requester_contact,
                            "Requester Category": s.requester_type,
                            "Expected Attendance": int(s.no_of_people) if str(s.no_of_people).isdigit() else 0,
                            "Assigned Volunteer": s.assigned_volunteer if s.assigned_volunteer else "⚠️ Unassigned",
                            "Status": s.status,
                            "Requested On": s.timestamp,
                        }
                        for s in upcoming_events
                    ]
                )

                st.dataframe(
                    df_upcoming,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Expected Attendance": st.column_config.NumberColumn(
                            "Expected Attendance",
                            format="%d ppl",
                        ),
                    },
                )

        with tab_stage:
            col_l, col_r = st.columns(2)

            with col_l:
                st.markdown("##### **Events by Life-Stage Category**")
                stage_counts = {
                    "🤰 Pre-natal (गर्भ-कालीन)": 0,
                    "👶 Childhood (बाल / शिशु)": 0,
                    "🎓 Education / Youth (शिक्षा / दीक्षा)": 0,
                    "💍 Grihastha & Social (गृहस्थ / सामाजिक)": 0,
                }
                for s in sanskar_list:
                    cat = _categorize_sanskar(s.sanskar_name)
                    stage_counts[cat] += 1

                fig_stage = go.Figure(
                    data=[
                        go.Bar(
                            y=list(stage_counts.keys()),
                            x=list(stage_counts.values()),
                            orientation="h",
                            marker_color=["#EC4899", "#3B82F6", "#10B981", "#F59E0B"],
                            text=list(stage_counts.values()),
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
                name_counts = {}
                for s in sanskar_list:
                    name = str(s.sanskar_name).title() or "Other"
                    name_counts[name] = name_counts.get(name, 0) + 1

                fig_names = go.Figure(
                    data=[
                        go.Bar(
                            x=list(name_counts.keys()),
                            y=list(name_counts.values()),
                            marker_color="#2d5a4a",
                            text=list(name_counts.values()),
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
                status_counts = {
                    "Pending": pending_sanskars,
                    "Fulfilled": fulfilled_sanskars,
                }

                fig_status = go.Figure(
                    data=[
                        go.Pie(
                            labels=list(status_counts.keys()),
                            values=list(status_counts.values()),
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
                vol_assignments = {}
                for s in sanskar_list:
                    vol = s.assigned_volunteer if s.assigned_volunteer else "Unassigned / Auto"
                    vol_assignments[vol] = vol_assignments.get(vol, 0) + 1

                fig_vol = go.Figure(
                    data=[
                        go.Bar(
                            x=list(vol_assignments.keys()),
                            y=list(vol_assignments.values()),
                            marker_color="#6366F1",
                            text=list(vol_assignments.values()),
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
            df_sanskar = pd.DataFrame(
                [
                    {
                        "Sanskar Name": s.sanskar_name,
                        "Category": _categorize_sanskar(s.sanskar_name),
                        "Occasion": s.occasion,
                        "Requester": s.requester_name,
                        "Contact": s.requester_contact,
                        "Type": s.requester_type,
                        "Attendance": int(s.no_of_people) if str(s.no_of_people).isdigit() else 0,
                        "Status": s.status,
                        "Assigned Volunteer": s.assigned_volunteer or "Unassigned",
                        "Timestamp": s.timestamp,
                    }
                    for s in sanskar_list
                ]
            )
            st.dataframe(df_sanskar, width="stretch", hide_index=True)
