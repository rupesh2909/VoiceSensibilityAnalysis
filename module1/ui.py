import streamlit as st

from module6.recommendation_ui import (
    render_recommendation
)

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
    get_customer,
    search_customers
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

    # -----------------------------------------------------
    # SESSION STATE
    # -----------------------------------------------------

    defaults = {
        "customer_mode": "search",
        "customer_id": "",
        "customer_name": "",
        "customer_segment": "RETAIL",
        "customer_value": "STANDARD"
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value

    # -----------------------------------------------------
    # CUSTOMER SEARCH DIALOG
    # -----------------------------------------------------

    @st.dialog(
        "🔍 Search Customer",
        width="small"
    )
    def customer_search_dialog():

        st.caption(
            "Search by customer name or customer ID."
        )

        search_term = st.text_input(
            "Customer",
            placeholder="Enter name or Customer ID"
        )

        if search_term.strip():

            customers = search_customers(
                search_term
            )

            if customers:

                st.markdown(
                    "#### Matching Customers"
                )

                options = {}

                for customer in customers:

                    customer_id = customer[0]
                    customer_name = (
                        customer[1]
                        or "Unnamed Customer"
                    )

                    segment = (
                        customer[2]
                        or "RETAIL"
                    )

                    value = (
                        customer[3]
                        or "STANDARD"
                    )

                    label = (
                        f"{customer_name}  ·  "
                        f"{customer_id}\n"
                        f"{segment}  ·  {value}"
                    )

                    options[label] = customer

                selected_label = st.radio(
                    "Select customer",
                    list(options.keys()),
                    index=None
                )

                if st.button(
                    "Select Customer",
                    type="primary",
                    use_container_width=True,
                    disabled=(
                        selected_label is None
                    )
                ):

                    selected = options[
                        selected_label
                    ]

                    st.session_state[
                        "customer_id"
                    ] = selected[0] or ""

                    st.session_state[
                        "customer_name"
                    ] = selected[1] or ""

                    st.session_state[
                        "customer_segment"
                    ] = selected[2] or "RETAIL"

                    st.session_state[
                        "customer_value"
                    ] = selected[3] or "STANDARD"

                    st.session_state[
                        "customer_mode"
                    ] = "existing"

                    st.rerun()

            else:

                st.warning(
                    "No matching customer found."
                )

                st.caption(
                    "You can add this customer as a new record."
                )

                if st.button(
                    "➕ Add New Customer",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state[
                        "customer_mode"
                    ] = "new"

                    st.session_state[
                        "customer_id"
                    ] = ""

                    st.session_state[
                        "customer_name"
                    ] = ""

                    st.session_state[
                        "customer_segment"
                    ] = "RETAIL"

                    st.session_state[
                        "customer_value"
                    ] = "STANDARD"

                    st.rerun()

    # -----------------------------------------------------
    # ROW 1
    # -----------------------------------------------------

    col_id, col_name = st.columns(
        [1, 1],
        gap="medium"
    )

    with col_id:

        st.markdown(
            "Customer ID"
        )

        search_label = (
            "🔍  "
            + (
                st.session_state[
                    "customer_id"
                ]
                or "Search customer..."
            )
        )

        if st.button(
            search_label,
            use_container_width=True,
            key="customer_search_button"
        ):

            customer_search_dialog()

    with col_name:

        st.text_input(
            "Customer Name",
            key="customer_name",
            disabled=(
                st.session_state[
                    "customer_mode"
                ] != "new"
            ),
            placeholder="Customer name"
        )

    # -----------------------------------------------------
    # ROW 2
    # -----------------------------------------------------

    col_segment, col_value = st.columns(
        [1, 1],
        gap="medium"
    )

    with col_segment:

        st.selectbox(
            "Customer Segment",
            [
                "RETAIL",
                "PREMIUM",
                "SME",
                "CORPORATE"
            ],
            key="customer_segment",
            disabled=(
                st.session_state[
                    "customer_mode"
                ] != "new"
            )
        )

    with col_value:

        from config.settings import (
            CUSTOMER_VALUE_OPTIONS
        )

        st.selectbox(
            "Customer Value",
            CUSTOMER_VALUE_OPTIONS,
            key="customer_value",
            disabled=(
                st.session_state[
                    "customer_mode"
                ] != "new"
            )
        )

    # -----------------------------------------------------
    # NEW CUSTOMER MODE
    # -----------------------------------------------------

    if (
        st.session_state[
            "customer_mode"
        ] == "new"
    ):

        st.caption(
            "New customer — enter the customer details "
            "above. A Customer ID will be generated "
            "automatically."
        )

        if st.button(
            "🔍 Search Existing Customer",
            use_container_width=True,
            key="search_existing_customer"
        ):

            st.session_state[
                "customer_mode"
            ] = "search"

            st.session_state[
                "customer_id"
            ] = ""

            st.session_state[
                "customer_name"
            ] = ""

            st.session_state[
                "customer_segment"
            ] = "RETAIL"

            st.session_state[
                "customer_value"
            ] = "STANDARD"

            st.rerun()

    # -----------------------------------------------------
    # RETURN CUSTOMER
    # -----------------------------------------------------

    return {

        "customer_id":
            st.session_state[
                "customer_id"
            ].strip(),

        "customer_name":
            st.session_state[
                "customer_name"
            ].strip(),

        "customer_segment":
            st.session_state[
                "customer_segment"
            ],

        "customer_value":
            st.session_state[
                "customer_value"
            ]
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

            # st.success(
            #     f"Selected: {uploaded_file.name}"
            # )

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

            st.markdown(
                """
                <style>
                div[data-testid="stRadio"] > div[role="radiogroup"] {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    column-gap: 30px;
                    row-gap: 8px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )            

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

                # st.success(
                #     f"Selected: {selected_name}"
                # )

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

def get_tool_summary(
    module,
    result
):

    if not result:
        return ""

    # Some tools may return:
    # {
    #     "success": True,
    #     "result": {...}
    # }
    #
    # Unwrap that structure if present.

    if isinstance(result, dict):

        nested_result = result.get(
            "result"
        )

        if isinstance(
            nested_result,
            dict
        ):

            result = nested_result

    # -----------------------------------------------------
    # TRANSCRIPTION
    # -----------------------------------------------------

    if module == "transcribe_call":

        segments = result.get(
            "segments_created"
        )

        if segments is not None:

            return (
                f"{segments} speech segments created"
            )

    # -----------------------------------------------------
    # DIARIZATION
    # -----------------------------------------------------

    elif module == "diarize_call":

        speaker_count = result.get(
            "speaker_count"
        )

        if speaker_count is not None:

            return (
                f"{speaker_count} speaker(s) detected"
            )

    # -----------------------------------------------------
    # ALIGNMENT
    # -----------------------------------------------------

    elif module == "align_transcript_with_speakers":

        segments = result.get(
            "segments_created"
        )

        if segments is not None:

            return (
                f"{segments} conversation segments aligned"
            )

    # -----------------------------------------------------
    # SENTIMENT
    # -----------------------------------------------------

    elif module == "analyze_customer_sentiment":

        sentiment = result.get(
            "sentiment"
        )

        score = result.get(
            "score"
        )

        if sentiment:

            if score is not None:

                return (
                    f"{str(sentiment).title()} "
                    f"· {float(score) * 100:.0f}% confidence"
                )

            return str(
                sentiment
            ).title()

    # -----------------------------------------------------
    # EMOTION
    # -----------------------------------------------------

    elif module == "analyze_customer_emotion":

        emotion = result.get(
            "primary_emotion"
        )

        score = result.get(
            "emotion_score"
        )

        if emotion:

            if score is not None:

                return (
                    f"{str(emotion).title()} "
                    f"· {float(score) * 100:.0f}% intensity"
                )

            return str(
                emotion
            ).title()

    # -----------------------------------------------------
    # ROOT CAUSE
    # -----------------------------------------------------

    elif module == "identify_dissatisfaction_root_cause":

        category = result.get(
            "root_cause_category"
        )

        severity = result.get(
            "severity"
        )

        if category:

            detail = str(
                category
            )

            if severity:

                detail += (
                    f" · {str(severity).upper()}"
                )

            return detail

    # -----------------------------------------------------
    # CHURN RISK
    # -----------------------------------------------------

    elif module == "analyze_customer_churn_risk":

        score = result.get(
            "churn_risk_score"
        )

        level = result.get(
            "churn_risk_level"
        )

        if score is not None:

            detail = str(
                score
            )

            if level:

                detail += (
                    f" / 100 · "
                    f"{str(level).upper()}"
                )

            else:

                detail += " / 100"

            return detail

    return ""

def render_live_progress(
    placeholder,
    messages,
    analysis_completed=False
):

    tool_info = {

        "transcribe_call": {
            "label": "Transcription",
            "description":
                "Extracting timestamped speech segments"
        },

        "diarize_call": {
            "label": "Speaker Detection",
            "description":
                "Identifying speakers and when they are talking"
        },

        "align_transcript_with_speakers": {
            "label": "Speaker Alignment",
            "description":
                "Matching speech segments with detected speakers"
        },

        "analyze_customer_sentiment": {
            "label": "Sentiment Analysis",
            "description":
                "Determining the customer's sentiment"
        },

        "analyze_customer_emotion": {
            "label": "Emotion Analysis",
            "description":
                "Detecting frustration, anger, disappointment and confusion"
        },

        "identify_dissatisfaction_root_cause": {
            "label": "Root Cause Analysis",
            "description":
                "Identifying the primary reason for dissatisfaction"
        },

        "analyze_customer_churn_risk": {
            "label": "Churn Risk Analysis",
            "description":
                "Evaluating churn risk and recovery priority"
        }
    }

    tool_order = [

        "transcribe_call",

        "diarize_call",

        "align_transcript_with_speakers",

        "analyze_customer_sentiment",

        "analyze_customer_emotion",

        "identify_dissatisfaction_root_cause",

        "analyze_customer_churn_risk"
    ]

    # =====================================================
    # LATEST STATE FOR EACH TOOL
    # =====================================================

    latest = {}

    for item in messages:

        module = item.get(
            "module",
            ""
        )

        if module in tool_info:

            latest[module] = item

    # =====================================================
    # SENTIMENT
    # =====================================================

    sentiment_label = ""

    sentiment_item = latest.get(
        "analyze_customer_sentiment"
    )

    if sentiment_item:

        sentiment_result = sentiment_item.get(
            "result"
        )

        if isinstance(
            sentiment_result,
            dict
        ):

            nested_result = (
                sentiment_result.get(
                    "result"
                )
            )

            if isinstance(
                nested_result,
                dict
            ):

                sentiment_result = nested_result

            sentiment_label = str(
                sentiment_result.get(
                    "sentiment",
                    ""
                )
            ).upper()

    # =====================================================
    # RENDER
    # =====================================================

    with placeholder.container():

        columns = st.columns(
            7,
            gap="small"
        )

        completed = 0

        for column, module in zip(
            columns,
            tool_order
        ):

            with column:

                item = latest.get(
                    module
                )

                info = tool_info[
                    module
                ]

                label = info[
                    "label"
                ]

                description = info[
                    "description"
                ]

                # =========================================
                # TOOL HAS AN EVENT
                # =========================================

                if item is not None:

                    status = item.get(
                        "status",
                        "running"
                    )

                    result = item.get(
                        "result"
                    )

                    # -------------------------------------
                    # RUNNING
                    # -------------------------------------

                    if status == "running":

                        st.info(
                            f"🔄 **{label}**\n\n"
                            f"{description}"
                        )

                    # -------------------------------------
                    # SUCCESS
                    # -------------------------------------

                    elif status == "success":

                        completed += 1

                        summary = get_tool_summary(
                            module,
                            result
                        )

                        detail = (
                            summary
                            if summary
                            else
                            "Processing completed successfully."
                        )

                        st.success(
                            f"✓ **{label}**\n\n"
                            f"{detail}"
                        )

                    # -------------------------------------
                    # ERROR
                    # -------------------------------------

                    elif status == "error":

                        st.error(
                            f"❌ **{label}**\n\n"
                            f"{item.get(
                                'message',
                                'Processing failed.'
                            )}"
                        )

                    # -------------------------------------
                    # UNKNOWN
                    # -------------------------------------

                    else:

                        st.info(
                            f"○ **{label}**\n\n"
                            f"{description}"
                        )

                # =========================================
                # NO EVENT YET
                # =========================================

                else:

                    # -------------------------------------
                    # CONDITIONAL TOOL SKIPPED
                    # ONLY AFTER COMPLETE
                    # -------------------------------------

                    if (
                        analysis_completed
                        and module
                        == "identify_dissatisfaction_root_cause"
                    ):

                        if sentiment_label:

                            sentiment_text = (
                                sentiment_label.lower()
                            )

                            st.warning(
                                f"⊘ **{label}**\n\n"
                                f"Not run · Customer sentiment "
                                f"was {sentiment_text}"
                            )

                        else:

                            st.warning(
                                f"⊘ **{label}**\n\n"
                                "Not run · Root cause "
                                "analysis was not required"
                            )

                    elif (
                        analysis_completed
                        and module
                        == "analyze_customer_churn_risk"
                    ):

                        st.warning(
                            f"⊘ **{label}**\n\n"
                            "Not run · No dissatisfaction/"
                            "churn signal detected"
                        )

                    # -------------------------------------
                    # STILL WAITING
                    # -------------------------------------

                    else:

                        st.info(
                            f"○ **{label}**\n\n"
                            f"{description}"
                        )

        # =================================================
        # PROGRESS COUNT
        # =================================================

        total = len(
            tool_order
        )

        st.caption(
            f"**{completed} of {total}** "
            "analysis steps completed"
        )

# @st.dialog(
#     "🤖 AI Analysis",
#     width="small",
#     dismissible=True
# )
def open_live_analysis(
    call_id
):

    status_placeholder = st.empty()

    # st.subheader(
    #     "🤖 AI Analysis",
    #     anchor=False
    # )

    st.caption(
        f"Processing call `{call_id}`"
    )

    status_placeholder.info(
        "🔄 AI analysis in progress..."
    )    

    # -------------------------------------------------
    # Progress state
    # -------------------------------------------------

    progress_state = {}

    # -------------------------------------------------
    # Progress UI
    # -------------------------------------------------

    progress_placeholder = st.empty()

    def progress_callback(
        progress
    ):

        module = progress.get(
            "module",
            ""
        )

        progress_state[
            module
        ] = progress

        # ---------------------------------------------
        # Immediately redraw the 7 cards
        # ---------------------------------------------

        render_live_progress(
            progress_placeholder,
            list(
                progress_state.values()
            ),
            analysis_completed=False
        )

    # -------------------------------------------------
    # Run agent
    # -------------------------------------------------

    try:

        from agents.conversation_agent import (
            ConversationAgent
        )

        agent = ConversationAgent(
            progress_callback=
                progress_callback
        )

        result = agent.analyze_call(
            call_id
        )

        # =================================================
        # FINAL PROGRESS SNAPSHOT
        # =================================================

        final_progress = {}

        for event in result.get(
            "execution_trace",
            []
        ):

            tool_name = event.get(
                "tool"
            )

            tool_result = event.get(
                "result"
            )

            if not tool_name:
                continue

            if isinstance(
                tool_result,
                dict
            ) and tool_result.get(
                "success",
                False
            ):

                final_progress[
                    tool_name
                ] = {

                    "module":
                        tool_name,

                    "status":
                        "success",

                    "message":
                        "Processing completed successfully.",

                    "result":
                        tool_result
                }

            else:

                final_progress[
                    tool_name
                ] = {

                    "module":
                        tool_name,

                    "status":
                        "error",

                    "message":
                        (
                            tool_result.get(
                                "error",
                                "Processing failed."
                            )
                            if isinstance(
                                tool_result,
                                dict
                            )
                            else
                            "Processing failed."
                        ),

                    "result":
                        tool_result
                }

        # ---------------------------------------------
        # Render final state
        # ---------------------------------------------

        render_live_progress(
            progress_placeholder,
            list(
                final_progress.values()
            ),
            analysis_completed=True
        )        

        # ---------------------------------------------
        # Final status
        # ---------------------------------------------

        if result.get(
            "action"
        ) == "final":

            status_placeholder.success(
                "✅ Analysis completed successfully."
            )

            st.session_state[
                "analysis_completed"
            ] = True

            st.session_state[
                "analysis_result"
            ] = result

            # -------------------------------------------------
            # Recommendation Engine
            # -------------------------------------------------

            render_recommendation(
                result.get(
                    "recommendation_decision"
                )
            )            

    except Exception as e:

        status_placeholder.error(
            f"❌ Analysis failed: {e}"
        )                     
                        
# def render_analysis_results(
#     placeholder,
#     messages
# ):

#     results = {}

#     for item in messages:

#         if item.get("status") != "success":
#             continue

#         module = item.get(
#             "module",
#             ""
#         )

#         result = item.get(
#             "result"
#         )

#         if not result:
#             continue

#         # Unwrap nested result if necessary
#         if isinstance(result, dict):

#             nested_result = result.get(
#                 "result"
#             )

#             if isinstance(
#                 nested_result,
#                 dict
#             ):

#                 result = nested_result

#         results[module] = result

#     if not results:
#         return

#     with placeholder.container():

#         st.markdown(
#             "### 📊 Analysis Results"
#         )

#         # =================================================
#         # SENTIMENT + EMOTION
#         # =================================================

#         sentiment = results.get(
#             "analyze_customer_sentiment"
#         )

#         emotion = results.get(
#             "analyze_customer_emotion"
#         )

#         if sentiment or emotion:

#             col1, col2 = st.columns(2)

#             # ---------------------------------------------
#             # Sentiment
#             # ---------------------------------------------

#             with col1:

#                 if sentiment:

#                     sentiment_label = sentiment.get(
#                         "sentiment",
#                         "N/A"
#                     )

#                     sentiment_score = sentiment.get(
#                         "score"
#                     )

#                     st.markdown(
#                         "#### Sentiment"
#                     )

#                     if sentiment_score is not None:

#                         st.metric(
#                             "Customer Sentiment",
#                             str(
#                                 sentiment_label
#                             ).title(),
#                             f"{float(sentiment_score) * 100:.0f}%"
#                         )

#                     else:

#                         st.metric(
#                             "Customer Sentiment",
#                             str(
#                                 sentiment_label
#                             ).title()
#                         )

#             # ---------------------------------------------
#             # Emotion
#             # ---------------------------------------------

#             with col2:

#                 if emotion:

#                     emotion_label = emotion.get(
#                         "primary_emotion",
#                         "N/A"
#                     )

#                     emotion_score = emotion.get(
#                         "emotion_score"
#                     )

#                     st.markdown(
#                         "#### Emotion"
#                     )

#                     if emotion_score is not None:

#                         st.metric(
#                             "Primary Emotion",
#                             str(
#                                 emotion_label
#                             ).title(),
#                             f"{float(emotion_score) * 100:.0f}%"
#                         )

#                     else:

#                         st.metric(
#                             "Primary Emotion",
#                             str(
#                                 emotion_label
#                             ).title()
#                         )

#         # =================================================
#         # ROOT CAUSE
#         # =================================================

#         root_cause = results.get(
#             "identify_dissatisfaction_root_cause"
#         )

#         if root_cause:

#             st.markdown(
#                 "#### 🔎 Dissatisfaction Root Cause"
#             )

#             col1, col2 = st.columns(2)

#             with col1:

#                 st.metric(
#                     "Category",
#                     root_cause.get(
#                         "root_cause_category",
#                         "N/A"
#                     )
#                 )

#             with col2:

#                 st.metric(
#                     "Severity",
#                     str(
#                         root_cause.get(
#                             "severity",
#                             "N/A"
#                         )
#                     ).upper()
#                 )

#             cause = root_cause.get(
#                 "root_cause"
#             )

#             if cause:

#                 st.info(
#                     cause
#                 )

#         # =================================================
#         # CHURN RISK
#         # =================================================

#         churn = results.get(
#             "analyze_customer_churn_risk"
#         )

#         if churn:

#             st.markdown(
#                 "#### ⚠️ Churn Risk"
#             )

#             col1, col2, col3 = st.columns(3)

#             with col1:

#                 st.metric(
#                     "Risk Score",
#                     f"{churn.get('churn_risk_score', 'N/A')} / 100"
#                 )

#             with col2:

#                 st.metric(
#                     "Risk Level",
#                     str(
#                         churn.get(
#                             "churn_risk_level",
#                             "N/A"
#                         )
#                     ).upper()
#                 )

#             with col3:

#                 st.metric(
#                     "Priority",
#                     str(
#                         churn.get(
#                             "recovery_priority",
#                             "N/A"
#                         )
#                     ).upper()
#                 )

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

    if (
        st.session_state.get(
            "customer_mode"
        ) == "new"
    ):

        if not customer["customer_name"]:

            st.warning(
                "Please enter the customer name."
            )

            return

        # ---------------------------------------------
        # Create new customer
        # ---------------------------------------------

        from .customer_repository import (
            create_customer
        )

        customer_id = create_customer(
            customer_name=customer[
                "customer_name"
            ],
            customer_segment=customer[
                "customer_segment"
            ],
            customer_value=customer[
                "customer_value"
            ]
        )

        customer[
            "customer_id"
        ] = customer_id

        st.session_state[
            "customer_id"
        ] = customer_id

        st.session_state[
            "customer_mode"
        ] = "existing"

    else:

        customer_record = get_customer(
            customer["customer_id"]
        )

        if customer_record is None:

            st.error(
                f"Customer ID `{customer['customer_id']}` "
                "was not found."
            )

            st.info(
                "Use Search Customer to select an existing "
                "customer or add a new customer."
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

    # =====================================================
    # AGENTIC ANALYSIS
    # =====================================================

    st.session_state[
        "analysis_job_id"
    ] = call_id

    st.session_state[
        "analysis_completed"
    ] = False

    st.session_state[
        "analysis_result"
    ] = None    

    # -----------------------------------------------------
    # Start background worker
    # -----------------------------------------------------

    open_live_analysis(
        call_id
    )    


