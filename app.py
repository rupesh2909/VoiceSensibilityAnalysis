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
    "Call recording analysis system"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "Development / Testing"
)

mode = st.sidebar.radio(
    "Mode",
    [
        "Development",
        "Full Pipeline"
    ]
)

render_reset_database()


# =========================================================
# DEVELOPMENT MODE
# =========================================================

if mode == "Development":

    selected_module = st.sidebar.radio(
        "Select module",
        [
            "Module 1",
            "Module 2",
            "Module 3",
            "Module 4",
            "Module 5",
            "Module 6",
            "Module 7",
            "Agentic Analysis"
        ]
    )

    st.sidebar.divider()

    # -----------------------------------------------------
    # MODULE 1
    # -----------------------------------------------------

    if selected_module == "Module 1":

        st.sidebar.info(
            "Tests file selection, "
            "validation and upload."
        )

        # Lazy import
        from module1.ui import run_module1

        run_module1()

    # -----------------------------------------------------
    # MODULE 2
    # -----------------------------------------------------

    elif selected_module == "Module 2":

        st.sidebar.info(
            "Uses files already uploaded "
            "by Module 1."
        )

        # Lazy import
        from module2.ui import run_module2

        run_module2()

    # -----------------------------------------------------
    # MODULE 3
    # -----------------------------------------------------

    elif selected_module == "Module 3":

        st.sidebar.info(
            "Uses CUSTOMER conversation "
            "already diarized by Module 2."
        )

        # Lazy import
        from module3.ui import run_module3

        run_module3()

    # -----------------------------------------------------
    # MODULE 4
    # -----------------------------------------------------

    elif selected_module == "Module 4":

        st.sidebar.info(
            "Uses CUSTOMER text and sentiment "
            "already processed by Module 3."
        )

        # Lazy imports
        from module4.ui import run_module4

        from module4.processing_service import (
            RootCauseProcessingService
        )

        service = (
            RootCauseProcessingService()
        )

        run_module4(
            service
        )

    # -----------------------------------------------------
    # MODULE 5
    # -----------------------------------------------------

    elif selected_module == "Module 5":

        st.sidebar.info(
            "Detects customer emotions "
            "from CUSTOMER conversation."
        )

        from module5.ui import run_module5

        run_module5()    

    # -----------------------------------------------------
    # MODULE 6
    # -----------------------------------------------------

    elif selected_module == "Module 6":

        st.sidebar.info(
            "Calculates customer churn risk "
            "and retention recommendations."
        )

        from module6.ui import (
            run_module6
        )

        run_module6()        

    # -----------------------------------------------------
    # MODULE 7
    # -----------------------------------------------------

    elif selected_module == "Module 7":

        st.sidebar.info(
            "Manager dashboard with "
            "prioritized customer recovery queue."
        )

        from module7.ui import (
            run_module7
        )

        run_module7()        

    # =========================================================
    # AGENTIC ANALYSIS
    # =========================================================

    elif selected_module == "Agentic Analysis":

        from agents.ui import (
            run_agentic_analysis
        )

        run_agentic_analysis()


# =========================================================
# FULL PIPELINE MODE
# =========================================================

else:

    st.sidebar.info(
        "Module 1 → Module 2 → Module 3 → Module 4 + Module 5"
    )

    st.subheader(
        "Full Pipeline"
    )

    st.write(
        "Full pipeline execution will be added "
        "after the individual modules are verified."
    )

    st.info(
        "For development, use Development mode "
        "and test each module independently."
    )