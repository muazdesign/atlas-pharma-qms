"""
Atlas Pharma QMS — CAPA Tracker
Logging corrective and preventive actions for claimed tickets.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_reviews_by_status, insert_capa, get_all_capa_logs


def render():
    user = st.session_state.get("user", {})
    role = user.get("role", "")

    st.markdown("""
    <h1 style="color: #0056b3; margin-bottom: 4px;">🛠️ CAPA Tracker</h1>
    <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">
        Log root causes, corrective actions, and preventive measures to resolve quality issues.
    </p>
    """, unsafe_allow_html=True)

    # ── New CAPA Resolution ───────────────────────────────────────────────
    if role == "Quality Manager":
        st.subheader("Resolve a Claimed Ticket")
        claimed = get_reviews_by_status("Claimed")
        if not claimed:
            st.info("No claimed tickets available for resolution. Claim a ticket from the Triage Inbox first.")
        else:
            claimed_list = [dict(r) for r in claimed]
            ticket_options = {
                f"#{r['id']} — {r['batch_number']} ({r['product_type']})": r["id"]
                for r in claimed_list
            }

            with st.form("capa_form", clear_on_submit=True):
                selected = st.selectbox("Select Claimed Ticket", options=list(ticket_options.keys()))

                # Show the complaint text
                selected_id = ticket_options[selected]
                ticket_detail = next((r for r in claimed_list if r["id"] == selected_id), None)
                if ticket_detail:
                    st.markdown(f"""
                    <div style="
                        background: #fff8f0;
                        border: 1px solid #ffc107;
                        border-radius: 8px;
                        padding: 12px 16px;
                        margin-bottom: 12px;
                    ">
                        <strong>Complaint:</strong> {ticket_detail['review_text']}
                    </div>
                    """, unsafe_allow_html=True)

                root_cause = st.text_area(
                    "Root Cause Analysis *",
                    placeholder="Describe the identified root cause of the quality issue...",
                    height=100,
                )
                corrective_action = st.text_area(
                    "Corrective Action *",
                    placeholder="What immediate actions were taken to fix the issue?",
                    height=100,
                )
                preventive_action = st.text_area(
                    "Preventive Action *",
                    placeholder="What measures will prevent recurrence?",
                    height=100,
                )

                resolve_btn = st.form_submit_button(
                    "✅  Resolve & Log CAPA",
                    use_container_width=True,
                    type="primary",
                )

            if resolve_btn:
                if not root_cause.strip() or not corrective_action.strip() or not preventive_action.strip():
                    st.error("All fields are required.")
                else:
                    insert_capa(
                        review_id=selected_id,
                        root_cause=root_cause.strip(),
                        corrective_action=corrective_action.strip(),
                        preventive_action=preventive_action.strip(),
                        manager_assigned=user["username"],
                    )
                    st.success(f"✅ Ticket #{selected_id} resolved and CAPA logged successfully!")
                    st.balloons()
                    st.rerun()
    else:
        st.info("Only Quality Managers can log CAPA resolutions.")

    st.markdown("---")

    # ── CAPA History ──────────────────────────────────────────────────────
    st.subheader("📜 Resolution History")
    capa_logs = get_all_capa_logs()
    if not capa_logs:
        st.info("No CAPA resolutions logged yet.")
        return

    for log in capa_logs:
        log_dict = dict(log)
        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid #e8edf2;
            border-left: 4px solid #28a745;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-weight: 600; color: #333;">CAPA #{log_dict['id']}</span>
                    <span style="color: #888; margin: 0 8px;">→</span>
                    <span style="color: #555;">Ticket #{log_dict['review_id']} | {log_dict['batch_number']}</span>
                </div>
                <span style="
                    background: #d4edda;
                    color: #155724;
                    padding: 2px 10px;
                    border-radius: 50px;
                    font-size: 0.75rem;
                    font-weight: 600;
                ">Resolved</span>
            </div>
            <div style="margin-top: 12px; font-size: 0.88rem; color: #555; line-height: 1.6;">
                <strong>🔍 Root Cause:</strong> {log_dict['root_cause']}<br/>
                <strong>🔧 Corrective Action:</strong> {log_dict['corrective_action']}<br/>
                <strong>🛡️ Preventive Action:</strong> {log_dict['preventive_action']}<br/>
                <span style="color: #aaa; font-size: 0.8rem;">
                    Resolved by {log_dict['manager_assigned']} on {log_dict['resolved_at']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
