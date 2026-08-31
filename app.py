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
        padding-top: 1.25rem;
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
        "📊 Manager Dashboard",
        anchor=False
    )

    st.info(
        "Module 7 — Manager Dashboard will be "
        "implemented here."
    )