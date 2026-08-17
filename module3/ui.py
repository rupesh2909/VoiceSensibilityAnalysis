import streamlit as st

from datetime import datetime

from database.database import (
    get_connection
)

from .sentiment_service import (
    SentimentService
)


def get_calls_with_diarization():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT DISTINCT
                c.call_id,
                c.file_name
            FROM calls c

            INNER JOIN transcript_segments ts
                ON c.call_id = ts.call_id

            ORDER BY c.created_at
            """
        ).fetchall()

    return rows


def get_customer_text(
    call_id
):

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT text
            FROM transcript_segments
            WHERE call_id = ?
              AND speaker = 'CUSTOMER'
            ORDER BY start_time
            """,
            (call_id,)
        ).fetchall()

    return " ".join(
        row[0]
        for row in rows
    )


def save_analysis(
    call_id,
    sentiment,
    score
):

    with get_connection() as conn:

        # -------------------------------------------------
        # Remove previous Module 3 result
        # -------------------------------------------------

        conn.execute(
            """
            DELETE FROM customer_analysis
            WHERE call_id = ?
            """,
            (call_id,)
        )

        # -------------------------------------------------
        # Save new result
        # -------------------------------------------------

        conn.execute(
            """
            INSERT INTO customer_analysis
            (
                call_id,
                sentiment,
                sentiment_score,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                call_id,
                sentiment,
                score,
                datetime.now().isoformat()
            )
        )

        conn.commit()


def run_module3():

    st.subheader(
        "Module 3 — Customer Sentiment Analysis"
    )

    # =====================================================
    # GET MODULE 2 RESULTS
    # =====================================================

    calls = (
        get_calls_with_diarization()
    )

    if not calls:

        st.warning(
            "No diarized conversations "
            "are available."
        )

        st.info(
            "Run Module 2 first."
        )

        return

    # =====================================================
    # SELECT CALLS
    # =====================================================

    selected_names = st.multiselect(
        "Select calls to analyze",
        [
            row[1]
            for row in calls
        ]
    )

    if not selected_names:

        return

    # =====================================================
    # RUN
    # =====================================================

    if not st.button(
        "▶ Run Module 3",
        type="primary"
    ):

        return

    service = SentimentService()

    for call_id, file_name in calls:

        if file_name not in selected_names:

            continue

        st.markdown(
            f"#### {file_name}"
        )

        status_box = st.empty()

        try:

            # -------------------------------------------------
            # Get CUSTOMER text only
            # -------------------------------------------------

            status_box.info(
                f"📖 Reading CUSTOMER "
                f"conversation — {file_name}"
            )

            customer_text = (
                get_customer_text(
                    call_id
                )
            )

            if not customer_text.strip():

                status_box.warning(
                    "No CUSTOMER text found."
                )

                continue

            # -------------------------------------------------
            # Sentiment
            # -------------------------------------------------

            status_box.info(
                f"🧠 Analyzing sentiment — "
                f"{file_name}"
            )

            result = service.analyze(
                customer_text
            )

            # -------------------------------------------------
            # Save
            # -------------------------------------------------

            save_analysis(
                call_id,
                result["sentiment"],
                result["score"]
            )

            status_box.success(
                f"✓ Module 3 completed — "
                f"{file_name}"
            )

            # -------------------------------------------------
            # Display
            # -------------------------------------------------

            col1, col2 = st.columns(2)

            col1.metric(
                "Sentiment",
                result["sentiment"]
            )

            col2.metric(
                "Confidence",
                f"{result['score']:.2%}"
            )

            with st.expander(
                "Customer text used for analysis"
            ):

                st.write(
                    customer_text
                )

        except Exception as e:

            status_box.error(
                f"❌ Module 3 failed: {e}"
            )