"""
Atlas Pharma QMS — Public Feedback Gateway
Allows any visitor to submit a product complaint or quality feedback.
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import insert_review
from services.gemini_ai import categorize_and_analyze


def render():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0056b3, #003d80);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 28px;
    ">
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">📝 Submit Quality Feedback</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 6px 0 0 0; font-size: 0.95rem;">
            Help us improve our products. Your feedback is reviewed by our quality team.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Information Box ──────────────────────────────────
    st.info(
        "**Your feedback matters.** Every submission is automatically analyzed by our AI system "
        "and routed to the appropriate quality manager for review and resolution."
    )

    # ── Feedback Form ────────────────────────────────────
    with st.form("feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            product_type = st.selectbox(
                "Product Type *",
                options=["Paracetamol Tablet 500 mg", "Paracetamol Syrup 120 mg/5 mL"],
                index=0,
            )
        with col2:
            batch_number = st.text_input(
                "Batch Number *",
                placeholder="e.g., BTX-2026-0420",
            )

        review_text = st.text_area(
            "Issue Description *",
            placeholder="Please describe the quality issue you observed in detail...",
            height=150,
        )

        st.markdown("---")
        submitted = st.form_submit_button(
            "🚀  Submit Feedback",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        # Validation
        if not batch_number.strip():
            st.error("⚠️ Please enter a valid batch number.")
            return
        if not review_text.strip() or len(review_text.strip()) < 10:
            st.error("⚠️ Please provide a detailed issue description (at least 10 characters).")
            return

        with st.spinner("🤖 Analyzing your feedback with AI..."):
            try:
                category, sentiment = categorize_and_analyze(review_text)
            except Exception:
                category, sentiment = "Major", "Neutral"

            insert_review(
                batch_number=batch_number.strip(),
                product_type=product_type,
                review_text=review_text.strip(),
                ai_category=category,
                ai_sentiment=sentiment,
            )

        # Success message
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border: 1px solid #28a745;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            margin-top: 16px;
        ">
            <h3 style="color: #155724; margin: 0 0 8px 0;">✅ Feedback Submitted Successfully</h3>
            <p style="color: #155724; margin: 0; font-size: 0.9rem;">
                <strong>Batch:</strong> {batch_number} &nbsp;|&nbsp;
                <strong>AI Category:</strong> {category} &nbsp;|&nbsp;
                <strong>Sentiment:</strong> {sentiment}
            </p>
            <p style="color: #555; margin: 8px 0 0 0; font-size: 0.85rem;">
                Your complaint has been logged and will be reviewed by our quality team.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.balloons()
