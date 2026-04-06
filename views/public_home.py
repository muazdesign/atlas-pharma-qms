"""
Atlas Pharma QMS — Public Landing Page
A clean, corporate homepage showcasing Atlas Pharma's quality commitment.
"""

import streamlit as st
import base64, os


def render():
    # ── Hero Section ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0056b3 0%, #003d80 50%, #002855 100%);
        border-radius: 16px;
        padding: 60px 40px;
        text-align: center;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; top: -50px; right: -50px;
            width: 200px; height: 200px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        "></div>
        <div style="
            position: absolute; bottom: -30px; left: -30px;
            width: 150px; height: 150px;
            background: rgba(255,255,255,0.03);
            border-radius: 50%;
        "></div>
        <h1 style="color: #ffffff; font-size: 2.8rem; margin-bottom: 12px; font-weight: 700; letter-spacing: -0.5px;">
            Atlas Pharma
        </h1>
        <p style="color: rgba(255,255,255,0.85); font-size: 1.2rem; margin-bottom: 28px; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.6;">
            Committed to manufacturing high-quality pharmaceutical products <br/> with uncompromising standards in safety, efficacy, and compliance.
        </p>
        <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
            <span style="
                background: rgba(255,255,255,0.15);
                color: white;
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
                backdrop-filter: blur(4px);
            ">🏭 GMP Certified</span>
            <span style="
                background: rgba(255,255,255,0.15);
                color: white;
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
                backdrop-filter: blur(4px);
            ">📋 ISO 9001:2015</span>
            <span style="
                background: rgba(255,255,255,0.15);
                color: white;
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
                backdrop-filter: blur(4px);
            ">🔬 ICH Compliant</span>
            <span style="
                background: rgba(255,255,255,0.15);
                color: white;
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
                backdrop-filter: blur(4px);
            ">🇹🇷 TİTCK Approved</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── What We Do ────────────────────────────────────────────────────────
    st.markdown("""
    <h2 style="text-align: center; color: #0056b3; margin-bottom: 8px; font-weight: 600;">
        What We Do
    </h2>
    <p style="text-align: center; color: #666; margin-bottom: 32px; font-size: 0.95rem;">
        From raw materials to finished dosage forms — quality at every step.
    </p>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    cards = [
        ("🔬", "Quality Assurance", "Every batch undergoes rigorous multi-stage testing before release, following strict pharmacopeial standards."),
        ("🤖", "AI-Powered Triage", "Our intelligent QMS automatically classifies and prioritizes product feedback using advanced AI models."),
        ("📊", "Real-Time Monitoring", "Live dashboards track quality metrics, complaint trends, and CAPA resolutions across all product lines."),
    ]
    for col, (icon, title, desc) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div style="
                background: #ffffff;
                border: 1px solid #e8edf2;
                border-radius: 12px;
                padding: 28px 20px;
                text-align: center;
                height: 220px;
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            ">
                <div style="font-size: 2.2rem; margin-bottom: 12px;">{icon}</div>
                <h3 style="color: #0056b3; font-size: 1.05rem; margin-bottom: 8px; font-weight: 600;">{title}</h3>
                <p style="color: #555; font-size: 0.85rem; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Key Figures ───────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0f5ff 0%, #e8edf5 100%);
        border-radius: 12px;
        padding: 32px 20px;
        margin-bottom: 32px;
    ">
        <h2 style="text-align: center; color: #0056b3; margin-bottom: 24px; font-weight: 600;">
            By the Numbers
        </h2>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 16px;">
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 2rem; font-weight: 700; color: #0056b3;">2</div>
                <div style="color: #666; font-size: 0.85rem;">Product Lines</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 2rem; font-weight: 700; color: #0056b3;">17</div>
                <div style="color: #666; font-size: 0.85rem;">Quality Parameters</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 2rem; font-weight: 700; color: #0056b3;">5</div>
                <div style="color: #666; font-size: 0.85rem;">Lab Partners</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 2rem; font-weight: 700; color: #0056b3;">24/7</div>
                <div style="color: #666; font-size: 0.85rem;">Quality Monitoring</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────
    st.markdown("""
    <h2 style="text-align: center; color: #0056b3; margin-bottom: 24px; font-weight: 600;">
        Quick Links
    </h2>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📝  Submit Feedback", use_container_width=True, key="home_feedback_btn"):
            st.session_state.public_page = "Feedback"
            st.rerun()
    with c2:
        if st.button("💊  View Products", use_container_width=True, key="home_catalog_btn"):
            st.session_state.public_page = "Catalog"
            st.rerun()
    with c3:
        if st.button("📞  Contact Us", use_container_width=True, key="home_contact_btn"):
            st.session_state.public_page = "Contact"
            st.rerun()
