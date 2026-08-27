import streamlit as st

from database.database import (
    get_connection
)

from agents.conversation_agent import (
    ConversationAgent
)


# =========================================================
# GET CALLS
# =========================================================

def get_available_calls():

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT
                call_id,
                file_name,
                status,
                created_at

            FROM calls

            ORDER BY created_at DESC
            """
        ).fetchall()


# =========================================================
# STATE
# =========================================================

def display_state(
    state
):

    st.markdown(
        "### Processing State"
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Transcription",
            (
                "✓ Complete"
                if state.get(
                    "transcription_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    with col2:

        st.metric(
            "Diarization",
            (
                "✓ Complete"
                if state.get(
                    "diarization_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    with col3:

        st.metric(
            "Alignment",
            (
                "✓ Complete"
                if state.get(
                    "alignment_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Sentiment",
            (
                "✓ Complete"
                if state.get(
                    "sentiment_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    with col2:

        st.metric(
            "Emotion",
            (
                "✓ Complete"
                if state.get(
                    "emotion_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    with col3:

        st.metric(
            "Root Cause",
            (
                "✓ Complete"
                if state.get(
                    "root_cause_complete",
                    False
                )
                else "✗ Pending"
            )
        )

    st.caption(
        f"Detected speakers: "
        f"{state.get('speaker_count', 0)}"
    )


# =========================================================
# FINAL ANALYSIS
# =========================================================

def display_final_analysis(
    analysis
):

    st.markdown(
        "## 🎯 Final Customer Intelligence"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Sentiment",
            analysis.get(
                "sentiment",
                "N/A"
            )
        )

    with col2:

        st.metric(
            "Emotion",
            analysis.get(
                "emotion",
                "N/A"
            )
        )

    with col3:

        st.metric(
            "Root Cause",
            analysis.get(
                "root_cause_category",
                "N/A"
            )
        )

    with col4:

        st.metric(
            "Severity",
            analysis.get(
                "severity",
                "N/A"
            )
        )

    # =====================================================
    # ROOT CAUSE
    # =====================================================

    st.markdown(
        "### Root Cause"
    )

    st.write(
        analysis.get(
            "root_cause",
            "Not determined"
        )
    )

    # =====================================================
    # DISSATISFACTION
    # =====================================================

    dissatisfied = str(
        analysis.get(
            "dissatisfied",
            "N/A"
        )
    ).upper()

    if dissatisfied == "YES":

        st.error(
            "⚠️ Customer dissatisfaction detected"
        )

    elif dissatisfied == "NO":

        st.success(
            "Customer does not appear dissatisfied"
        )

    # =====================================================
    # CONFIDENCE
    # =====================================================

    confidence = analysis.get(
        "confidence"
    )

    if confidence is not None:

        try:

            st.metric(
                "Root Cause Confidence",
                f"{float(confidence):.1%}"
            )

        except (
            TypeError,
            ValueError
        ):

            pass

    # =====================================================
    # EVIDENCE
    # =====================================================

    evidence = analysis.get(
        "evidence"
    )

    if evidence:

        with st.expander(
            "View supporting evidence"
        ):

            st.write(
                evidence
            )


# =========================================================
# MAIN
# =========================================================

def run_agentic_analysis():

    st.header(
        "🤖 Agentic Conversation Analysis"
    )

    st.caption(
        "Qwen3 decides which analytical "
        "tool should execute next."
    )

    # =====================================================
    # CALLS
    # =====================================================

    calls = (
        get_available_calls()
    )

    if not calls:

        st.warning(
            "No calls are available."
        )

        st.info(
            "Upload a call using Module 1 first."
        )

        return

    call_options = {

        (
            f"{row['file_name']} | "
            f"{row['call_id']}"
        ):
            row["call_id"]

        for row in calls
    }

    selected_call = st.selectbox(
        "Select a call",
        options=list(
            call_options.keys()
        )
    )

    call_id = call_options[
        selected_call
    ]

    # =====================================================
    # CURRENT STATE
    # =====================================================

    from tools.database_tool import (
        DatabaseTool
    )

    state_tool = (
        DatabaseTool()
    )

    current_state = (
        state_tool.run(
            call_id
        )
    )

    display_state(
        current_state
    )

    st.divider()

    # =====================================================
    # RUN AGENT
    # =====================================================

    if not st.button(
        "🤖 Run Agentic Analysis",
        type="primary",
        use_container_width=True
    ):

        return

    try:

        with st.spinner(
            "Qwen3 agent is analyzing the call..."
        ):

            agent = (
                ConversationAgent()
            )

            result = (
                agent.analyze_call(
                    call_id
                )
            )

        # =================================================
        # EXECUTION TRACE
        # =================================================

        st.markdown(
            "## 🤖 Agent Execution Trace"
        )

        trace = result.get(
            "execution_trace",
            []
        )

        if not trace:

            st.info(
                "No tools were required. "
                "The call was already analyzed."
            )

        for event in trace:

            tool = event.get(
                "tool",
                "Unknown"
            )

            reason = event.get(
                "reason",
                ""
            )

            status = event.get(
                "status"
            )

            if status == "success":

                st.success(
                    f"✓ {tool}"
                )

            else:

                st.error(
                    f"✗ {tool}"
                )

            if reason:

                st.caption(
                    f"Reason: {reason}"
                )

        # =================================================
        # RESULT
        # =================================================

        if result.get(
            "action"
        ) == "final":

            display_final_analysis(
                result.get(
                    "analysis",
                    {}
                )
            )

        else:

            st.warning(
                "Agent stopped without "
                "producing a final analysis."
            )

            st.json(
                result
            )

    except Exception as e:

        st.error(
            "Agent execution failed."
        )

        st.exception(e)