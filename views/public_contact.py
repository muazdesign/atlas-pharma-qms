"""
Atlas Pharma QMS — Contact Us Page (Static)
Displays company contact information.
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
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">📞 Contact Us</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 6px 0 0 0; font-size: 0.95rem;">
            We'd love to hear from you. Reach out to our team anytime.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    # ── Contact Information ──────────────────────────────────────────────
    with col_left:
        st.markdown("""
        <div style="
            background: #f8faff;
            border-radius: 12px;
            padding: 28px;
            height: 100%;
        ">
            <h3 style="color: #0056b3; margin: 0 0 20px 0;">Get In Touch</h3>

            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.3rem;">🏢</span>
                    <div>
                        <div style="font-weight: 600; color: #333; font-size: 0.9rem;">Head Office</div>
                        <div style="color: #666; font-size: 0.85rem; line-height: 1.5;">
                            Atlas Pharma İlaç San. ve Tic. A.Ş.<br/>
                            Organize Sanayi Bölgesi, No: 42<br/>
                            34906 Pendik, İstanbul, Türkiye
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.3rem;">📧</span>
                    <div>
                        <div style="font-weight: 600; color: #333; font-size: 0.9rem;">Email</div>
                        <div style="color: #666; font-size: 0.85rem;">info@atlaspharma.com.tr</div>
                        <div style="color: #666; font-size: 0.85rem;">quality@atlaspharma.com.tr</div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.3rem;">📱</span>
                    <div>
                        <div style="font-weight: 600; color: #333; font-size: 0.9rem;">Phone</div>
                        <div style="color: #666; font-size: 0.85rem;">+90 (216) 555 42 00</div>
                        <div style="color: #666; font-size: 0.85rem;">Mon – Fri, 09:00 – 18:00 (GMT+3)</div>
                    </div>
                </div>
            </div>

            <div>
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 1.3rem;">🌐</span>
                    <div>
                        <div style="font-weight: 600; color: #333; font-size: 0.9rem;">Website</div>
                        <div style="color: #666; font-size: 0.85rem;">www.atlaspharma.com.tr</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Contact Form (Visual only — static/demo) ─────────────────────────
    with col_right:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e0e5ec;
            border-radius: 12px;
            padding: 28px;
        ">
            <h3 style="color: #0056b3; margin: 0 0 4px 0;">Send a Message</h3>
            <p style="color: #999; font-size: 0.8rem; margin: 0 0 16px 0;">Demo form — messages are not sent.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("contact_form", clear_on_submit=True):
            name = st.text_input("Your Name", placeholder="Full name")
            email = st.text_input("Your Email", placeholder="you@example.com")
            subject = st.selectbox("Subject", [
                "General Inquiry",
                "Product Question",
                "Quality / Regulatory",
                "Partnership Opportunity",
                "Other",
            ])
            message = st.text_area("Message", placeholder="How can we help you?", height=120)
            send = st.form_submit_button("📤  Send Message", use_container_width=True, type="primary")

        if send:
            if name.strip() and email.strip() and message.strip():
                st.success("✅ Thank you for your message! Our team will get back to you shortly.")
            else:
                st.warning("Please fill in all required fields.")

    # ── Map placeholder ──────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0f5ff, #e0eaff);
        border-radius: 12px;
        padding: 40px;
        text-align: center;
    ">
        <span style="font-size: 2.5rem;">🗺️</span>
        <h3 style="color: #0056b3; margin: 12px 0 4px 0;">Visit Us</h3>
        <p style="color: #666; font-size: 0.9rem;">
            Organize Sanayi Bölgesi, No: 42 — Pendik, İstanbul, Türkiye
        </p>
    </div>
    """, unsafe_allow_html=True)
