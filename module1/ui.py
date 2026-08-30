import streamlit as st

from config.settings import (
    SAMPLE_FILES_DIR
)

from .validation_service import (
    validate_file
)

from .upload_service import (
    save_uploaded_file,
    copy_sample_file
)

from .call_repository import (
    create_call
)

from .customer_repository import (
    get_customer
)


# =========================================================
# SAMPLE FILES
# =========================================================

def get_sample_files():

    if not SAMPLE_FILES_DIR.exists():

        return []

    return sorted(
        [
            file
            for file in SAMPLE_FILES_DIR.iterdir()
            if file.is_file()
        ],
        key=lambda x: x.name.lower()
    )


# =========================================================
# CUSTOMER INFORMATION
# =========================================================

def render_customer_information():

    st.markdown(
        "### 👤 Customer Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        customer_id = st.text_input(
            "Customer ID",
            placeholder="e.g. CUST-FC88BB8F"
        )
    
    with col2:

        customer_name = st.text_input(
            "Customer Name",
            placeholder="Enter customer name"
        )

    col1, col2 = st.columns(2)

    with col1:

        customer_segment = st.selectbox(
            "Customer Segment",
            [
                "RETAIL",
                "PREMIUM",
                "SME",
                "CORPORATE"
            ]
        )

    with col2:

        customer_value = st.selectbox(
            "Customer Value",
            [
                "STANDARD",
                "SILVER",
                "GOLD",
                "PLATINUM"
            ]
        )

    return {
        "customer_id": customer_id.strip(),
        "customer_name": customer_name.strip(),
        "customer_segment": customer_segment,
        "customer_value": customer_value
    }


# =========================================================
# FILE SELECTION
# =========================================================

def render_file_selection():

    st.markdown(
        "### 🎧 Call Recording"
    )

    tab_upload, tab_samples = st.tabs(
        [
            "⬆️ Upload Audio",
            "🎵 Sample Audio"
        ]
    )

    selected_source = None
    selected_file = None

    # -----------------------------------------------------
    # UPLOAD
    # -----------------------------------------------------

    with tab_upload:

        uploaded_file = st.file_uploader(
            "Upload call recording",
            type=[
                "mp3",
                "wav",
                "m4a",
                "mp4",
                "aac",
                "flac"
            ],
            accept_multiple_files=False,
            help="Maximum file size: 200 MB"
        )

        if uploaded_file is not None:

            selected_source = "UPLOAD"
            selected_file = uploaded_file

            st.success(
                f"Selected: {uploaded_file.name}"
            )

    # -----------------------------------------------------
    # SAMPLE FILES
    # -----------------------------------------------------

    with tab_samples:

        sample_files = get_sample_files()

        if not sample_files:

            st.warning(
                "No sample audio files found."
            )

        else:

            sample_options = {
                file.name: file
                for file in sample_files
            }

            selected_name = st.radio(
                "Available sample recordings",
                options=list(
                    sample_options.keys()
                ),
                index=None
            )

            if selected_name:

                selected_source = "SAMPLE"
                selected_file = sample_options[
                    selected_name
                ]

                st.success(
                    f"Selected: {selected_name}"
                )

    return (
        selected_source,
        selected_file
    )


# =========================================================
# PROCESS FILE
# =========================================================

def process_selected_file(
    selected_source,
    selected_file,
    customer_id
):

    file_name = selected_file.name

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    if selected_source == "SAMPLE":

        file_size = (
            selected_file.stat().st_size
        )

    else:

        file_size = selected_file.size

    with st.status(
        "Preparing call for analysis...",
        expanded=True
    ) as status:

        st.write(
            "🔍 Validating audio file..."
        )

        valid, message = validate_file(
            file_name,
            file_size
        )

        if not valid:

            st.error(message)

            status.update(
                label="Audio validation failed",
                state="error"
            )

            return None

        st.write(
            "✓ Audio validation completed"
        )

        # -------------------------------------------------
        # Save audio
        # -------------------------------------------------

        st.write(
            "💾 Preparing audio for analysis..."
        )

        try:

            if selected_source == "SAMPLE":

                audio_path = copy_sample_file(
                    selected_file
                )

            else:

                audio_path = save_uploaded_file(
                    selected_file
                )

            st.write(
                "✓ Audio file ready"
            )

            # -------------------------------------------------
            # Database
            # -------------------------------------------------

            st.write(
                "🗄️ Creating call record..."
            )

            call_id = create_call(
                file_name=file_name,
                file_path=audio_path,
                file_size=file_size,
                source=selected_source,
                customer_id=customer_id
            )

            st.write(
                f"✓ Call created: `{call_id}`"
            )

            status.update(
                label="Call ready for analysis",
                state="complete"
            )

            return call_id

        except Exception as e:

            st.error(
                str(e)
            )

            status.update(
                label="Failed to prepare call",
                state="error"
            )

            return None

def render_live_progress(
    placeholder,
    messages
):

    with placeholder.container():

        st.markdown(
            "### 🤖 Live Analysis"
        )

        if not messages:

            st.caption(
                "Waiting for analysis to begin..."
            )

            return

        for item in messages:

            status = item.get(
                "status",
                "running"
            )

            message = item.get(
                "message",
                "Processing..."
            )

            if status == "running":

                st.markdown(
                    f"🔄 **{message}**"
                )

            elif status == "success":

                st.markdown(
                    f"✓ {message}"
                )

            elif status == "error":

                st.markdown(
                    f"❌ {message}"
                )

# =========================================================
# MAIN
# =========================================================

def run_module1():

    st.caption(
        "Upload a recording or select a sample call "
        "to begin AI-powered customer analysis."
    )    

    # =====================================================
    # INPUT AREA
    # =====================================================

    col_file, col_customer = st.columns(
        [1.35, 1],
        gap="large"
    )

    with col_file:

        selected_source, selected_file = (
            render_file_selection()
        )

    with col_customer:

        customer = (
            render_customer_information()
        )

    # =====================================================
    # ANALYZE
    # =====================================================

    col1, col2, col3 = st.columns(
        [1.2, 1.6, 1.2]
    )

    with col2:

        analyze_clicked = st.button(
            "🚀 Analyze Call",
            type="primary",
            use_container_width=True
        )

    if not analyze_clicked:

        return

    # =====================================================
    # VALIDATION
    # =====================================================

    if selected_file is None:

        st.warning(
            "Please upload a call recording or "
            "select a sample recording."
        )

        return

    if not customer["customer_name"]:

        st.warning(
            "Please enter the customer name."
        )

        return

    # =====================================================
    # CUSTOMER VALIDATION
    # =====================================================

    customer_record = get_customer(
        customer["customer_id"]
    )

    if customer_record is None:

        st.error(
            f"Customer ID `{customer['customer_id']}` "
            "was not found."
        )

        st.info(
            "For now, please enter an existing Customer ID."
        )

        return

    # =====================================================
    # CREATE CALL
    # =====================================================

    call_id = process_selected_file(
        selected_source,
        selected_file,
        customer["customer_id"]
    )

    if not call_id:

        return

    # =====================================================
    # CUSTOMER INFORMATION
    # =====================================================

    st.session_state[
        "current_call_id"
    ] = call_id

    st.session_state[
        "current_customer"
    ] = customer

    st.session_state[
        "analysis_started"
    ] = True

    st.success(
        f"Call `{call_id}` is ready. "
        "Starting AI analysis..."
    )

    # =====================================================
    # AGENTIC ANALYSIS
    # =====================================================

    from agents.conversation_agent import (
        ConversationAgent
    )

    progress_messages = []

    progress_placeholder = st.empty()


    def update_progress(event):

        progress_messages.append(
            event
        )

        render_live_progress(
            progress_placeholder,
            progress_messages
        )    

    try:

        agent = ConversationAgent(
            progress_callback=update_progress
        )

        result = agent.analyze_call(
            call_id
        )

        # Store result for subsequent reruns
        st.session_state[
            "analysis_result"
        ] = result

        st.session_state[
            "analysis_complete"
        ] = True

        # -------------------------------------------------
        # Basic execution result
        # -------------------------------------------------

        if result.get("action") == "final":

            analysis = result.get(
                "analysis",
                {}
            )

            if analysis.get("status") == "TOOL_FAILED":

                st.error(
                    "❌ Analysis stopped because a tool failed."
                )

                st.json(
                    analysis
                )

            else:

                st.success(
                    "✅ Analysis completed successfully."
                )

                st.json(
                    result
                )

        else:

            st.warning(
                "The AI agent stopped without "
                "producing a final result."
            )

            st.json(
                result
            )

    except Exception as e:

        st.error(
            "❌ AI analysis failed."
        )

        st.exception(e)