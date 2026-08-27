import streamlit as st


def run_module4(
    processing_service
):

    st.subheader(
        "Module 4 — Dissatisfaction Root Cause"
    )

    st.caption(
        "Analyze calls already processed "
        "by Module 3."
    )

    # =====================================================
    # GET MODULE 3 CALLS
    # =====================================================

    calls = (
        processing_service
        .get_calls_for_analysis()
    )

    if not calls:

        st.warning(
            "No calls are available for Module 4."
        )

        st.info(
            "Run Module 3 first."
        )

        return

    # =====================================================
    # FILE SELECTION
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
        "Select file(s) to analyze",
        options=list(
            call_options.keys()
        )
    )

    if not selected_files:

        st.info(
            "Select one or more files."
        )

        return

    # =====================================================
    # RUN
    # =====================================================

    if not st.button(
        "▶ Run Module 4",
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
    # PROCESS FILES
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
            f"🔍 Analyzing {file_name}..."
        )

        try:

            result = (
                processing_service
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
                f"❌ Module 4 failed for "
                f"{file_name}: {e}"
            )

        progress.progress(
            (index + 1) / total
        )

    status.success(
        "Module 4 processing completed."
    )

    # =====================================================
    # RESULTS
    # =====================================================

    if not results:

        return

    st.subheader(
        "Dissatisfaction Root Cause Results"
    )

    for file_name, result in results:

        st.markdown(
            f"### {file_name}"
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:
            st.markdown("Dissatisfaction")
            st.write(result["dissatisfaction"])

            # st.metric(
            #     "Dissatisfaction",
            #     result[
            #         "dissatisfaction"
            #     ]
            # )

        with col2:
            st.markdown("Root Cause")
            st.write(result["category"])

            # st.metric(
            #     "Root Cause",
            #     result[
            #         "category"
            #     ]
            # )

        with col3:

            st.markdown("Severity")
            st.write(result["severity"])
            

        with col4:
            st.markdown("Confidence")
            st.write(f"{result['confidence']:.1%}")

            # st.metric(
            #     "Confidence",
            #     f"{result['confidence']:.1%}"
            # )

        st.write(
            f"Sentiment: "
            f"**{result['sentiment']}**"
        )

        st.divider()