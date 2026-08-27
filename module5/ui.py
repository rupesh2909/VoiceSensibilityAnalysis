import streamlit as st

from module5.processing_service import (
    EmotionProcessingService
)


def run_module5():

    st.subheader(
        "Module 5 — Customer Emotion Detection"
    )

    st.caption(
        "Detects anger, frustration, disappointment "
        "and confusion from the CUSTOMER conversation."
    )

    # =====================================================
    # SERVICE
    # =====================================================

    service = (
        EmotionProcessingService()
    )

    # =====================================================
    # AVAILABLE CALLS
    # =====================================================

    calls = (
        service
        .get_calls_for_analysis()
    )

    if not calls:

        st.warning(
            "No CUSTOMER conversations are available."
        )

        st.info(
            "Run Module 2 first."
        )

        return

    # =====================================================
    # CALL SELECTION
    # =====================================================

    call_options = {}

    for row in calls:

        call_id = row["call_id"]

        file_name = row["file_name"]

        display_name = (
            f"{file_name} | {call_id}"
        )

        call_options[
            display_name
        ] = call_id

    selected_files = st.multiselect(
        "Select call(s) to analyze",
        options=list(
            call_options.keys()
        )
    )

    if not selected_files:

        st.info(
            "Select one or more calls."
        )

        return

    # =====================================================
    # RUN
    # =====================================================

    if not st.button(
        "▶ Run Module 5",
        type="primary"
    ):

        return

    progress = st.progress(0)

    status = st.empty()

    results = []

    total = len(
        selected_files
    )

    # =====================================================
    # PROCESS
    # =====================================================

    for index, display_name in enumerate(
        selected_files
    ):

        call_id = (
            call_options[
                display_name
            ]
        )

        file_name = display_name.split(
            " | ",
            1
        )[0]

        status.info(
            f"🧠 Detecting customer emotion — "
            f"{file_name}"
        )

        try:

            result = (
                service
                .process_call(
                    call_id
                )
            )

            results.append(
                (
                    file_name,
                    result
                )
            )

            status.success(
                f"✓ Completed — {file_name}"
            )

        except Exception as e:

            st.error(
                f"❌ Module 5 failed for "
                f"{file_name}: {e}"
            )

        progress.progress(
            (index + 1) / total
        )

    status.success(
        "Module 5 processing completed."
    )

    # =====================================================
    # DISPLAY RESULTS
    # =====================================================

    if not results:

        return

    st.subheader(
        "Customer Emotion Results"
    )

    for file_name, result in results:

        st.markdown(
            f"### {file_name}"
        )

        # -------------------------------------------------
        # Main metrics
        # -------------------------------------------------

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Primary Emotion",
                result[
                    "primary_emotion"
                ]
            )

        with col2:

            st.metric(
                "Confidence",
                f"{result['confidence']:.1%}"
            )

        with col3:

            st.metric(
                "Emotion Intensity",
                f"{result['emotion_intensity']:.1%}"
            )

        # -------------------------------------------------
        # Target emotions
        # -------------------------------------------------

        st.markdown(
            "#### Customer Emotion Breakdown"
        )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        with c1:

            st.metric(
                "😡 Anger",
                f"{result['anger_score']:.1%}"
            )

        with c2:

            st.metric(
                "😤 Frustration",
                f"{result['frustration_score']:.1%}"
            )

        with c3:

            st.metric(
                "😞 Disappointment",
                f"{result['disappointment_score']:.1%}"
            )

        with c4:

            st.metric(
                "😕 Confusion",
                f"{result['confusion_score']:.1%}"
            )

        # -------------------------------------------------
        # Additional emotions
        # -------------------------------------------------

        with st.expander(
            "Additional emotion signals"
        ):

            c1, c2, c3, c4, c5 = (
                st.columns(5)
            )

            c1.metric(
                "Fear",
                f"{result['fear_score']:.1%}"
            )

            c2.metric(
                "Sadness",
                f"{result['sadness_score']:.1%}"
            )

            c3.metric(
                "Neutral",
                f"{result['neutral_score']:.1%}"
            )

            c4.metric(
                "Joy",
                f"{result['joy_score']:.1%}"
            )

            c5.metric(
                "Surprise",
                f"{result['surprise_score']:.1%}"
            )

        # -------------------------------------------------
        # Business interpretation
        # -------------------------------------------------

        emotion = result[
            "primary_emotion"
        ]

        intensity = result[
            "emotion_intensity"
        ]

        if emotion == "ANGER":

            st.error(
                f"🔴 High customer anger detected "
                f"({intensity:.1%})"
            )

        elif emotion == "FRUSTRATION":

            st.warning(
                f"🟠 Customer frustration detected "
                f"({intensity:.1%})"
            )

        elif emotion == "DISAPPOINTMENT":

            st.warning(
                f"🟡 Customer disappointment detected "
                f"({intensity:.1%})"
            )

        elif emotion == "CONFUSION":

            st.info(
                f"🔵 Customer confusion detected "
                f"({intensity:.1%})"
            )

        st.divider()