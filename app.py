import streamlit as st

from dotenv import load_dotenv

from config.settings import (
    APP_TITLE,
    APP_ICON,
    PAGE_LAYOUT
)

from database.database import (
    initialize_database
)


# =========================================================
# INITIALIZATION
# =========================================================

load_dotenv()

initialize_database()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=PAGE_LAYOUT,
    initial_sidebar_state="collapsed"
)


# =========================================================
# GLOBAL UI
# =========================================================

st.markdown(
    """
    <style>

    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Use more of the screen */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        max-width: 1500px;
    }

    /* Compact page title */
    h1 {
        margin-top: 0;
        margin-bottom: 0.1rem;
        padding-top: 0;
        line-height: 1.15;
    }

    /* Compact caption below title */
    .block-container p {
        margin-bottom: 0.35rem;
    }

    /* Compact tabs */
    .stTabs {
        margin-top: 0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        margin-bottom: 0;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 7px 18px;
    }

    /* Reduce vertical gaps between Streamlit blocks */
    .element-container {
        margin-bottom: 0.25rem;
    }

    /* =====================================================
    LIVE ANALYSIS
    ===================================================== */

    .live-step {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 7px 12px;
        margin-bottom: 5px;
        border-radius: 8px;
        font-size: 0.92rem;
    }
    
    .live-detail {
        font-size: 0.78rem;
        opacity: 0.65;
        margin-top: 2px;
}    

    .live-icon {
        width: 20px;
        text-align: center;
        font-weight: 700;
    }

    .live-status {
        margin-left: auto;
        font-size: 0.78rem;
        opacity: 0.65;
    }

    .live-step.completed {
        opacity: 0.8;
    }

    .live-step.failed {
        opacity: 0.9;
    }

    .live-step.running {
        font-weight: 600;
    }

    .live-step.running .live-icon {
        animation: livePulse 1.2s ease-in-out infinite;
    }

    @keyframes livePulse {
        0% {
            opacity: 0.35;
            transform: scale(0.9);
        }

        50% {
            opacity: 1;
            transform: scale(1.15);
        }

        100% {
            opacity: 0.35;
            transform: scale(0.9);
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    "## 🎧 Voice Sensibility Analysis"
)

st.caption(
    "AI-powered customer conversation intelligence "
    "and recovery system"
)


# =========================================================
# TOP NAVIGATION
# =========================================================

tab_analyze, tab_dashboard = st.tabs(
    [
        "📁 Analyze Call",
        "📊 Manager Dashboard"
    ]
)


# =========================================================
# ANALYZE CALL
# =========================================================

with tab_analyze:

    from module1.ui import run_module1

    run_module1()


# =========================================================
# MANAGER DASHBOARD
# =========================================================

with tab_dashboard:

    st.header(
        "📊 Manager Dashboard"
    )

    st.info(
        "Module 7 — Manager Dashboard will be "
        "implemented here."
    )