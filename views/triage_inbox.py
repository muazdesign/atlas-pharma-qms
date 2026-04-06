"""
Atlas Pharma QMS — AI Triage Inbox
Active workspace for Quality Managers to review and claim incoming complaints.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_all_reviews, claim_review


def render():
    user = st.session_state.get("user", {})
    role = user.get("role", "")

    st.markdown("""
    <h1 style="color: #0056b3; margin-bottom: 4px;">🤖 AI Triage Inbox</h1>
    <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">
        Review AI-categorized complaints. Claim tickets to begin investigation.
    </p>
    """, unsafe_allow_html=True)

    reviews = get_all_reviews()
    if not reviews:
        st.info("📭 No reviews in the system yet.")
        return

    df = pd.DataFrame([dict(r) for r in reviews])

    # ── Filters ───────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns(3)
    with f1:
        filter_status = st.selectbox("Filter by Status", ["All", "Open", "Claimed", "Resolved"])
    with f2:
        filter_category = st.selectbox("Filter by Category", ["All", "Critical", "Major", "Minor"])
    with f3:
        filter_product = st.selectbox("Filter by Product", ["All"] + list(df["product_type"].unique()))

    filtered = df.copy()
    if filter_status != "All":
        filtered = filtered[filtered["status"] == filter_status]
    if filter_category != "All":
        filtered = filtered[filtered["ai_category"] == filter_category]
    if filter_product != "All":
        filtered = filtered[filtered["product_type"] == filter_product]

    # ── Summary Metrics ──────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Showing", len(filtered))
    m2.metric("Critical", len(filtered[filtered["ai_category"] == "Critical"]) if len(filtered) > 0 else 0)
    m3.metric("Open", len(filtered[filtered["status"] == "Open"]) if len(filtered) > 0 else 0)
    m4.metric("Claimed", len(filtered[filtered["status"] == "Claimed"]) if len(filtered) > 0 else 0)

    st.markdown("---")

    # ── Review Cards ──────────────────────────────────────────────────────
    if filtered.empty:
        st.info("No reviews match your filters.")
        return

    for _, row in filtered.iterrows():
        # Color coding for categories
        cat_colors = {"Critical": "#dc3545", "Major": "#fd7e14", "Minor": "#ffc107", "Pending": "#6c757d"}
        status_colors = {"Open": "#dc3545", "Claimed": "#fd7e14", "Resolved": "#28a745"}
        cat_color = cat_colors.get(row["ai_category"], "#6c757d")
        status_color = status_colors.get(row["status"], "#6c757d")

        border_color = "#dc3545" if row["ai_category"] == "Critical" else "#e8edf2"

        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid {border_color};
            border-left: 4px solid {cat_color};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            {'box-shadow: 0 0 12px rgba(220,53,69,0.15);' if row['ai_category'] == 'Critical' else 'box-shadow: 0 1px 4px rgba(0,0,0,0.04);'}
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-weight: 600; color: #333;">#{row['id']}</span>
                    <span style="color: #888; margin: 0 8px;">|</span>
                    <span style="color: #555;">{row['batch_number']}</span>
                    <span style="color: #888; margin: 0 8px;">|</span>
                    <span style="color: #555; font-size: 0.85rem;">{row['product_type']}</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span style="
                        background: {cat_color}15;
                        color: {cat_color};
                        padding: 2px 10px;
                        border-radius: 50px;
                        font-size: 0.75rem;
                        font-weight: 600;
                    ">{row['ai_category']}</span>
                    <span style="
                        background: {status_color}15;
                        color: {status_color};
                        padding: 2px 10px;
                        border-radius: 50px;
                        font-size: 0.75rem;
                        font-weight: 600;
                    ">{row['status']}</span>
                </div>
            </div>
            <p style="color: #555; font-size: 0.88rem; margin: 8px 0 4px 0; line-height: 1.5;">
                {row['review_text'][:200]}{'...' if len(str(row['review_text'])) > 200 else ''}
            </p>
            <div style="color: #aaa; font-size: 0.75rem;">
                {'Claimed by: ' + str(row['claimed_by']) + ' | ' if row['claimed_by'] else ''}
                Sentiment: {row.get('ai_sentiment', 'N/A')} | {row['created_at']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Claim button (only for QMs on Open tickets)
        if row["status"] == "Open" and role == "Quality Manager":
            if st.button(f"✋ Claim Ticket #{row['id']}", key=f"claim_{row['id']}"):
                claim_review(row["id"], user["username"])
                st.success(f"Ticket #{row['id']} claimed by {user['full_name']}.")
                st.rerun()
