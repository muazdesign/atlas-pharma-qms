"""
Atlas Pharma QMS — Public Product Catalog
Displays Paracetamol products with specs and Trendyol buy links.
"""

import streamlit as st


def render():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0056b3, #003d80);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 28px;
    ">
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">💊 Product Catalog</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 6px 0 0 0; font-size: 0.95rem;">
            Explore our pharmaceutical product range — quality you can trust.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Product 1: Paracetamol Tablet ─────────────────────────────────────
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f0f5ff, #e0eaff);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div>
                <div style="font-size: 4rem;">💊</div>
                <div style="color: #0056b3; font-weight: 600; margin-top: 8px;">Tablet Form</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="
            background: #ffffff;
            border: 1px solid #e0e5ec;
            border-radius: 12px;
            padding: 24px;
            height: 240px;
        ">
            <h3 style="color: #0056b3; margin: 0 0 4px 0;">Paracetamol Tablet 500 mg</h3>
            <span style="
                background: #e8f5e9; color: #2e7d32;
                padding: 2px 10px; border-radius: 50px;
                font-size: 0.75rem; font-weight: 500;
            ">In Stock</span>
            <p style="color: #555; font-size: 0.9rem; margin-top: 12px; line-height: 1.6;">
                White to off-white, round, biconvex film-coated tablets containing 500 mg of paracetamol (acetaminophen).
                Manufactured under strict GMP guidelines with full batch traceability.
            </p>
            <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px;">
                <span style="color: #777; font-size: 0.8rem;">🏷️ 500 mg per tablet</span>
                <span style="color: #777; font-size: 0.8rem;">📦 20 tablets / blister</span>
                <span style="color: #777; font-size: 0.8rem;">🧪 USP Compliant</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Product 1: Specs Table ────────────────────────────────────────────
    with st.expander("📋  View Quality Specifications — Paracetamol Tablet", expanded=False):
        st.markdown("""
        | Parameter | Specification | Test Method |
        |---|---|---|
        | Appearance | White to off-white, round, biconvex | Visual Inspection |
        | Average Weight | 550 ± 5% mg | USP ⟨791⟩ |
        | Hardness | 5 – 10 kp | Tablet Hardness Tester |
        | Friability | ≤ 1.0% | USP ⟨1216⟩ |
        | Disintegration | ≤ 15 minutes | USP ⟨701⟩ |
        | Assay | 95.0 – 105.0% | HPLC |
        | Dissolution | ≥ 80% in 30 min | USP ⟨711⟩ Apparatus II |
        """)

    if st.button("🛒  Buy on Trendyol", key="buy_tablet", use_container_width=True):
        st.markdown(
            '<meta http-equiv="refresh" content="0; url=https://www.trendyol.com">',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Product 2: Paracetamol Syrup ──────────────────────────────────────
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fff8f0, #ffe8d0);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div>
                <div style="font-size: 4rem;">🧴</div>
                <div style="color: #e67e22; font-weight: 600; margin-top: 8px;">Syrup Form</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="
            background: #ffffff;
            border: 1px solid #e0e5ec;
            border-radius: 12px;
            padding: 24px;
            height: 240px;
        ">
            <h3 style="color: #e67e22; margin: 0 0 4px 0;">Paracetamol Syrup 120 mg / 5 mL</h3>
            <span style="
                background: #e8f5e9; color: #2e7d32;
                padding: 2px 10px; border-radius: 50px;
                font-size: 0.75rem; font-weight: 500;
            ">In Stock</span>
            <p style="color: #555; font-size: 0.9rem; margin-top: 12px; line-height: 1.6;">
                Clear, cherry-flavored oral suspension containing 120 mg paracetamol per 5 mL.
                Designed for pediatric use with a calibrated measuring cup included. Preservative-controlled formula.
            </p>
            <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px;">
                <span style="color: #777; font-size: 0.8rem;">🏷️ 120 mg / 5 mL</span>
                <span style="color: #777; font-size: 0.8rem;">📦 100 mL bottle</span>
                <span style="color: #777; font-size: 0.8rem;">🍒 Cherry Flavor</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    with st.expander("📋  View Quality Specifications — Paracetamol Syrup", expanded=False):
        st.markdown("""
        | Parameter | Specification | Test Method |
        |---|---|---|
        | Appearance | Clear, colorless to pale-yellow liquid | Visual / Organoleptic |
        | pH | 4.5 – 6.5 | pH Meter (USP ⟨791⟩) |
        | Specific Gravity | 1.10 – 1.25 g/mL | Densitometer |
        | Assay | 90.0 – 110.0% | HPLC |
        | Volume | 100 mL ± 2% | Graduated Cylinder |
        | Viscosity | 50 – 200 cP | Brookfield Viscometer |
        | Microbial Limits | TAMC ≤ 10² CFU/mL | USP ⟨61⟩/⟨62⟩ |
        """)

    if st.button("🛒  Buy on Trendyol", key="buy_syrup", use_container_width=True):
        st.markdown(
            '<meta http-equiv="refresh" content="0; url=https://www.trendyol.com">',
            unsafe_allow_html=True,
        )
