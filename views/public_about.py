"""
Atlas Pharma QMS — About Us Page
Company mission, values, and team.
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
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">🏢 About Atlas Pharma</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 6px 0 0 0; font-size: 0.95rem;">
            Delivering quality healthcare products with integrity and innovation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mission ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: #f8faff;
        border-left: 4px solid #0056b3;
        padding: 24px 28px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 28px;
    ">
        <h3 style="color: #0056b3; margin: 0 0 8px 0;">Our Mission</h3>
        <p style="color: #444; font-size: 0.95rem; line-height: 1.7; margin: 0;">
            Atlas Pharma is dedicated to manufacturing safe, effective, and accessible pharmaceutical
            products for communities across Turkey and beyond. We combine modern manufacturing technology
            with rigorous quality management to ensure every product meets the highest pharmacopeial standards.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Core Values ──────────────────────────────────────────────────────
    st.markdown('<h2 style="color: #0056b3; font-weight: 600; margin-bottom: 16px;">Our Core Values</h2>', unsafe_allow_html=True)

    cols = st.columns(4)
    values = [
        ("🛡️", "Patient Safety", "Safety is non-negotiable. Every decision is made with the patient in mind."),
        ("✅", "Quality First", "We exceed regulatory requirements through continuous improvement and innovation."),
        ("🤝", "Integrity", "Transparency and honesty guide our relationships with partners and regulators."),
        ("🌱", "Sustainability", "We are committed to environmentally responsible manufacturing practices."),
    ]
    for col, (icon, title, desc) in zip(cols, values):
        with col:
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid #e8edf2;
                border-radius: 12px;
                padding: 20px 16px;
                text-align: center;
                min-height: 190px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            ">
                <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
                <h4 style="color: #0056b3; font-size: 0.95rem; margin-bottom: 6px;">{title}</h4>
                <p style="color: #666; font-size: 0.8rem; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Quality Commitment ───────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0f5ff, #e0eaff);
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 28px;
    ">
        <h2 style="color: #0056b3; text-align: center; margin-bottom: 16px;">Quality Management System</h2>
        <p style="color: #444; text-align: center; font-size: 0.95rem; line-height: 1.7; max-width: 700px; margin: 0 auto;">
            Our electronic QMS (eQMS) represents our commitment to digitising and automating the quality lifecycle.
            From AI-powered complaint triage to real-time CAPA tracking, every quality event is captured, analysed,
            and resolved with full audit trail visibility.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Team Section ─────────────────────────────────────────────────────
    st.markdown('<h2 style="color: #0056b3; font-weight: 600; margin-bottom: 16px;">Quality Team</h2>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e8edf2;
            border-radius: 12px;
            padding: 28px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        ">
            <div style="
                width: 80px; height: 80px;
                background: linear-gradient(135deg, #0056b3, #003d80);
                border-radius: 50%;
                margin: 0 auto 16px auto;
                display: flex; align-items: center; justify-content: center;
                font-size: 2rem; color: white;
            ">M</div>
            <h3 style="color: #333; margin: 0 0 4px 0;">Maimouna Diabi</h3>
            <p style="color: #0056b3; font-weight: 500; font-size: 0.85rem; margin: 0 0 12px 0;">Quality Manager — Product Specs</p>
            <p style="color: #666; font-size: 0.85rem; line-height: 1.5;">
                Oversees physical and functional product specifications for all Paracetamol dosage forms.
                Ensures compliance with USP monographs and ICH stability guidelines.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e8edf2;
            border-radius: 12px;
            padding: 28px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        ">
            <div style="
                width: 80px; height: 80px;
                background: linear-gradient(135deg, #0056b3, #003d80);
                border-radius: 50%;
                margin: 0 auto 16px auto;
                display: flex; align-items: center; justify-content: center;
                font-size: 2rem; color: white;
            ">B</div>
            <h3 style="color: #333; margin: 0 0 4px 0;">Büşra</h3>
            <p style="color: #0056b3; font-weight: 500; font-size: 0.85rem; margin: 0 0 12px 0;">Quality Manager — Lab Partners</p>
            <p style="color: #666; font-size: 0.85rem; line-height: 1.5;">
                Manages relationships with external testing laboratories and regulatory bodies (TSE, TÜBİTAK, TİTCK).
                Coordinates third-party audits and ISO/ISTA compliance.
            </p>
        </div>
        """, unsafe_allow_html=True)
