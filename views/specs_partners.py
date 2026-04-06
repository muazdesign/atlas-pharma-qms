"""
Atlas Pharma QMS — Product Specs & Lab Partners
Reference hub with searchable tables — internal view.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_all_specs, get_all_partners


def render():
    st.markdown("""
    <h1 style="color: #0056b3; margin-bottom: 4px;">📋 Product Specs & Lab Partners</h1>
    <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">
        The source of truth for quality parameters and testing partners.
    </p>
    """, unsafe_allow_html=True)

    tab_specs, tab_partners = st.tabs(["🔬  Product Specifications", "🏛️  Lab Partners & Regulators"])

    # ── Tab 1: Product Specifications ─────────────────────────────────────
    with tab_specs:
        specs = get_all_specs()
        if not specs:
            st.info("No specifications loaded. Run the seed script.")
            return

        df_specs = pd.DataFrame([dict(s) for s in specs])

        # Search + filter
        c1, c2 = st.columns([2, 1])
        with c1:
            search = st.text_input("🔍 Search specs", placeholder="Search by parameter, product, specification...")
        with c2:
            product_filter = st.selectbox("Filter by Product", ["All"] + list(df_specs["product_name"].unique()))

        filtered = df_specs.copy()
        if search.strip():
            mask = filtered.apply(lambda row: search.lower() in str(row).lower(), axis=1)
            filtered = filtered[mask]
        if product_filter != "All":
            filtered = filtered[filtered["product_name"] == product_filter]

        st.markdown(f"**{len(filtered)}** specifications found")
        st.dataframe(
            filtered[["product_name", "form", "parameter", "specification", "test_method"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_name": "Product",
                "form": "Form",
                "parameter": "Parameter",
                "specification": "Specification",
                "test_method": "Test Method",
            },
            height=450,
        )

    # ── Tab 2: Lab Partners & Regulators ──────────────────────────────────
    with tab_partners:
        partners = get_all_partners()
        if not partners:
            st.info("No partners loaded. Run the seed script.")
            return

        for p in partners:
            p_dict = dict(p)
            type_colors = {
                "Standards Body": "#0056b3",
                "Research Laboratory": "#6f42c1",
                "Regulatory Authority": "#dc3545",
                "Third-Party Testing": "#28a745",
            }
            type_color = type_colors.get(p_dict["type"], "#6c757d")

            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid #e8edf2;
                border-left: 4px solid {type_color};
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            ">
                <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap;">
                    <div>
                        <h3 style="color: #333; margin: 0 0 4px 0; font-size: 1.05rem;">{p_dict['institution_name']}</h3>
                        <span style="
                            background: {type_color}15;
                            color: {type_color};
                            padding: 2px 10px;
                            border-radius: 50px;
                            font-size: 0.75rem;
                            font-weight: 600;
                        ">{p_dict['type']}</span>
                    </div>
                </div>
                <div style="margin-top: 12px; font-size: 0.88rem; color: #555; line-height: 1.6;">
                    <strong>Standards:</strong> {p_dict['standards']}<br/>
                    <strong>Contact:</strong> {p_dict['contact_info']}<br/>
                    <strong>Notes:</strong> {p_dict['notes']}
                </div>
            </div>
            """, unsafe_allow_html=True)
