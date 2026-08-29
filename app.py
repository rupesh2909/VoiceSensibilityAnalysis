import streamlit as st

from dotenv import load_dotenv

from dev_tools.reset_database import (
    render_reset_database
)

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
    layout=PAGE_LAYOUT
)


# =========================================================
# HEADER
# =========================================================

st.title(
    "🎧 Voice Sensibility Analysis"
)

st.caption(
    "AI-powered customer conversation intelligence "
    "and recovery system"
)

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

st.sidebar.header(
    "Navigation"
)

selected_page = st.sidebar.radio(
    "Select",
    [
        "📁 Upload / Analyze Call",
        "📊 Manager Dashboard"
    ]
)

st.sidebar.divider()

# =========================================================
# CLEAR DATABASE
# =========================================================

render_reset_database()

st.sidebar.divider()


# =========================================================
# UPLOAD / ANALYZE
# =========================================================

if selected_page == "📁 Upload / Analyze Call":

    from module1.ui import run_module1

    from agents.ui import (
        run_agentic_analysis
    )

    st.header(
        "📁 Upload / Analyze Call"
    )

    run_module1()

    st.divider()

    run_agentic_analysis()


# =========================================================
# MANAGER DASHBOARD
# =========================================================

elif selected_page == "📊 Manager Dashboard":

    st.header(
        "📊 Manager Dashboard"
    )

    st.info(
        "Manager dashboard will be connected "
        "in the next step."
    )