"""
Atlas Pharma QMS — Staff Authentication (Gatekeeper)
Login form for internal QMS access.
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_user, verify_password


def render():
    st.markdown("<br/>" * 2, unsafe_allow_html=True)

    # Centered login card
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #0056b3, #003d80);
            padding: 32px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 24px;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">🔐</div>
            <h2 style="color: white; margin: 0; font-size: 1.5rem;">Staff Portal</h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.85rem; margin: 4px 0 0 0;">
                Internal access for authorized personnel only.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_btn = st.form_submit_button("🔑  Sign In", use_container_width=True, type="primary")

        if login_btn:
            if not username or not password:
                st.error("Please enter both username and password.")
                return

            user = get_user(username.strip().lower())
            if user and verify_password(password, user["password_hash"]):
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                }
                st.session_state.internal_page = "Dashboard"
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

        st.markdown("""
        <div style="text-align: center; margin-top: 16px;">
            <p style="color: #999; font-size: 0.8rem;">
                This portal is restricted to Atlas Pharma employees.<br/>
                If you need access, contact your system administrator.
            </p>
        </div>
        """, unsafe_allow_html=True)
