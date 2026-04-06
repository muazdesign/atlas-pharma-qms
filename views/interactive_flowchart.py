"""
Atlas Pharma QMS — Interactive Workflow Flowchart
Dynamic visual representation of the quality workflow that responds to ticket data.
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db_manager import get_status_counts, get_category_counts


def render():
    st.markdown("""
    <h1 style="color: #0056b3; margin-bottom: 4px;">🔄 Quality Workflow</h1>
    <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">
        Live pipeline view — each step reflects real-time ticket data.
    </p>
    """, unsafe_allow_html=True)

    status_counts = get_status_counts()
    cat_counts = get_category_counts()

    open_c = status_counts.get("Open", 0)
    claimed_c = status_counts.get("Claimed", 0)
    resolved_c = status_counts.get("Resolved", 0)
    total = open_c + claimed_c + resolved_c

    critical_c = cat_counts.get("Critical", 0)
    major_c = cat_counts.get("Major", 0)
    minor_c = cat_counts.get("Minor", 0)

    # ── Step color logic: brighter if there are active tickets ────────────
    def step_color(count, active_color, idle_color="#e0e5ec"):
        return active_color if count > 0 else idle_color

    def text_color(count, active="#ffffff", idle="#999"):
        return active if count > 0 else idle

    # ── Flowchart ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; gap: 0; flex-wrap: wrap; margin: 20px 0 32px 0;">

        <!-- Step 1: Feedback Received -->
        <div style="
            background: {step_color(total, '#0056b3')};
            color: {text_color(total)};
            padding: 24px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 150px;
            box-shadow: {'0 4px 16px rgba(0,86,179,0.3)' if total > 0 else 'none'};
            transition: all 0.3s;
        ">
            <div style="font-size: 1.8rem;">📥</div>
            <div style="font-weight: 600; font-size: 0.9rem; margin-top: 4px;">Feedback Received</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 4px;">{total}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">total tickets</div>
        </div>

        <!-- Arrow -->
        <div style="font-size: 1.5rem; color: #0056b3; padding: 0 8px;">➔</div>

        <!-- Step 2: AI Triage -->
        <div style="
            background: {step_color(open_c, '#dc3545')};
            color: {text_color(open_c)};
            padding: 24px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 150px;
            box-shadow: {'0 4px 16px rgba(220,53,69,0.3)' if open_c > 0 else 'none'};
            transition: all 0.3s;
        ">
            <div style="font-size: 1.8rem;">🤖</div>
            <div style="font-weight: 600; font-size: 0.9rem; margin-top: 4px;">AI Triage</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 4px;">{open_c}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">awaiting claim</div>
        </div>

        <!-- Arrow -->
        <div style="font-size: 1.5rem; color: #0056b3; padding: 0 8px;">➔</div>

        <!-- Step 3: Claimed / Investigation -->
        <div style="
            background: {step_color(claimed_c, '#fd7e14')};
            color: {text_color(claimed_c)};
            padding: 24px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 150px;
            box-shadow: {'0 4px 16px rgba(253,126,20,0.3)' if claimed_c > 0 else 'none'};
            transition: all 0.3s;
        ">
            <div style="font-size: 1.8rem;">🔍</div>
            <div style="font-weight: 600; font-size: 0.9rem; margin-top: 4px;">Investigation</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 4px;">{claimed_c}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">in progress</div>
        </div>

        <!-- Arrow -->
        <div style="font-size: 1.5rem; color: #0056b3; padding: 0 8px;">➔</div>

        <!-- Step 4: CAPA -->
        <div style="
            background: {step_color(claimed_c, '#6f42c1')};
            color: {text_color(claimed_c)};
            padding: 24px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 150px;
            box-shadow: {'0 4px 16px rgba(111,66,193,0.3)' if claimed_c > 0 else 'none'};
            transition: all 0.3s;
        ">
            <div style="font-size: 1.8rem;">🛠️</div>
            <div style="font-weight: 600; font-size: 0.9rem; margin-top: 4px;">CAPA</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 4px;">{claimed_c}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">pending resolution</div>
        </div>

        <!-- Arrow -->
        <div style="font-size: 1.5rem; color: #0056b3; padding: 0 8px;">➔</div>

        <!-- Step 5: Resolved -->
        <div style="
            background: {step_color(resolved_c, '#28a745')};
            color: {text_color(resolved_c)};
            padding: 24px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 150px;
            box-shadow: {'0 4px 16px rgba(40,167,69,0.3)' if resolved_c > 0 else 'none'};
            transition: all 0.3s;
        ">
            <div style="font-size: 1.8rem;">✅</div>
            <div style="font-weight: 600; font-size: 0.9rem; margin-top: 4px;">Resolved</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 4px;">{resolved_c}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">closed</div>
        </div>

    </div>
    """, unsafe_allow_html=True)

    # ── Category Breakdown ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("AI Category Breakdown")

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        st.markdown(f"""
        <div style="
            background: #dc354515;
            border: 1px solid #dc354530;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; font-weight: 700; color: #dc3545;">{critical_c}</div>
            <div style="color: #dc3545; font-weight: 600; font-size: 0.9rem;">🚨 Critical</div>
            <div style="color: #999; font-size: 0.75rem; margin-top: 4px;">Safety / Regulatory Risk</div>
        </div>
        """, unsafe_allow_html=True)
    with bc2:
        st.markdown(f"""
        <div style="
            background: #fd7e1415;
            border: 1px solid #fd7e1430;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; font-weight: 700; color: #fd7e14;">{major_c}</div>
            <div style="color: #fd7e14; font-weight: 600; font-size: 0.9rem;">⚠️ Major</div>
            <div style="color: #999; font-size: 0.75rem; margin-top: 4px;">Quality Deviation</div>
        </div>
        """, unsafe_allow_html=True)
    with bc3:
        st.markdown(f"""
        <div style="
            background: #ffc10715;
            border: 1px solid #ffc10730;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; font-weight: 700; color: #b8860b;">{minor_c}</div>
            <div style="color: #b8860b; font-weight: 600; font-size: 0.9rem;">💡 Minor</div>
            <div style="color: #999; font-size: 0.75rem; margin-top: 4px;">Low-Impact Observation</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Explanation ──────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: #f8faff;
        border-left: 4px solid #0056b3;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
    ">
        <strong style="color: #0056b3;">How the Workflow Operates:</strong>
        <ol style="color: #555; font-size: 0.88rem; line-height: 1.7; margin: 8px 0 0 0;">
            <li><strong>Feedback Received</strong> — A complaint is submitted via the public form.</li>
            <li><strong>AI Triage</strong> — Gemini AI categorizes it as Critical, Major, or Minor and assigns sentiment.</li>
            <li><strong>Investigation</strong> — A Quality Manager claims the ticket and begins root-cause analysis.</li>
            <li><strong>CAPA</strong> — Corrective and Preventive Actions are documented and logged.</li>
            <li><strong>Resolved</strong> — The ticket is closed with a full audit trail.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
