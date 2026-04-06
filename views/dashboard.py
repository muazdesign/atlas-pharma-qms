"""
Atlas Pharma QMS — Executive Dashboard
High-level analytics with Plotly charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_category_counts, get_status_counts, get_monthly_trend, get_all_reviews


def render():
    st.markdown("""
    <h1 style="color: #0056b3; margin-bottom: 4px;">📊 Executive Dashboard</h1>
    <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">
        Real-time quality metrics overview.
    </p>
    """, unsafe_allow_html=True)

    # ── KPI Counters ──────────────────────────────────────────────────────
    status_counts = get_status_counts()
    total = sum(status_counts.values())
    open_c = status_counts.get("Open", 0)
    claimed_c = status_counts.get("Claimed", 0)
    resolved_c = status_counts.get("Resolved", 0)

    k1, k2, k3, k4 = st.columns(4)
    kpis = [
        ("Total Tickets", total, "#0056b3"),
        ("Open", open_c, "#dc3545"),
        ("Claimed", claimed_c, "#fd7e14"),
        ("Resolved", resolved_c, "#28a745"),
    ]
    for col, (label, value, color) in zip([k1, k2, k3, k4], kpis):
        with col:
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid #e8edf2;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            ">
                <div style="font-size: 2rem; font-weight: 700; color: {color};">{value}</div>
                <div style="color: #666; font-size: 0.85rem; margin-top: 4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Charts Row ────────────────────────────────────────────────────────
    chart_left, chart_right = st.columns(2)

    # Pie chart: AI Categorization
    with chart_left:
        st.subheader("AI Categorization Breakdown")
        cat_counts = get_category_counts()
        if cat_counts:
            df_cat = pd.DataFrame(list(cat_counts.items()), columns=["Category", "Count"])
            color_map = {"Critical": "#dc3545", "Major": "#fd7e14", "Minor": "#ffc107", "Pending": "#6c757d"}
            fig_pie = px.pie(
                df_cat, names="Category", values="Count",
                color="Category",
                color_discrete_map=color_map,
                hole=0.45,
            )
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                font=dict(family="Inter, sans-serif"),
            )
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No review data yet.")

    # Line chart: Monthly Trend
    with chart_right:
        st.subheader("Monthly Issue Trend")
        trend = get_monthly_trend()
        if trend:
            df_trend = pd.DataFrame([dict(r) for r in trend])
            fig_line = px.line(
                df_trend, x="month", y="cnt",
                markers=True,
                labels={"month": "Month", "cnt": "Issues Reported"},
            )
            fig_line.update_traces(
                line=dict(color="#0056b3", width=3),
                marker=dict(size=8),
            )
            fig_line.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Tickets",
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No trend data yet.")

    # ── Status Breakdown Bar Chart ────────────────────────────────────────
    st.subheader("Ticket Status Overview")
    if status_counts:
        df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
        color_map_status = {"Open": "#dc3545", "Claimed": "#fd7e14", "Resolved": "#28a745"}
        fig_bar = px.bar(
            df_status, x="Status", y="Count", color="Status",
            color_discrete_map=color_map_status,
            text_auto=True,
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Recent Reviews Table ──────────────────────────────────────────────
    st.subheader("Latest Reviews")
    reviews = get_all_reviews()
    if reviews:
        df = pd.DataFrame([dict(r) for r in reviews[:10]])
        cols_show = ["id", "batch_number", "product_type", "ai_category", "status", "created_at"]
        cols_present = [c for c in cols_show if c in df.columns]
        st.dataframe(
            df[cols_present],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "batch_number": "Batch #",
                "product_type": "Product",
                "ai_category": "AI Category",
                "status": "Status",
                "created_at": "Created",
            },
        )
    else:
        st.info("No reviews submitted yet.")
