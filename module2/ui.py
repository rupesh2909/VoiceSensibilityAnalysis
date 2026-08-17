import streamlit as st

from module1.call_repository import (
    get_all_calls
)

from .processing_service import (
    ProcessingService
)


def run_module2(
    files=None
):

    st.subheader(
        "Module 2 — Transcription & Diarization"
    )

    # =====================================================
    # GET FILES FROM MODULE 1
    # =====================================================

    if files is None:

        database_calls = (
            get_all_calls()
        )

        files = [
            {
                "call_id": row[0],
                "file_name": row[1],
                "file_path": row[2]
            }
            for row in database_calls
        ]

    if not files:

        st.warning(
            "No files are available."
        )

        st.info(
            "Run Module 1 first."
        )

        return

    # =====================================================
    # FILE SELECTION
    # =====================================================

    file_names = [
        item["file_name"]
        for item in files
    ]

    selected_names = st.multiselect(
        "Select files to process",
        file_names
    )

    if not selected_names:

        return

    # =====================================================
    # RUN
    # =====================================================

    if not st.button(
        "▶ Run Module 2",
        type="primary"
    ):

        return

    service = ProcessingService()

    for item in files:

        if (
            item["file_name"]
            not in selected_names
        ):

            continue

        call_id = item["call_id"]

        file_name = item["file_name"]

        file_path = item["file_path"]

        st.markdown(
            f"#### {file_name}"
        )

        status_box = st.empty()

        def update_progress(
            action
        ):

            messages = {

                "CONVERTING":
                    f"🔄 Converting {file_name}...",

                "TRANSCRIBING":
                    f"🎙️ Transcribing {file_name}...",

                "DIARIZING":
                    f"🗣️ Diarizing {file_name}...",

                "ALIGNING":
                    f"🔗 Aligning speakers with "
                    f"transcription...",

                "COMPLETED":
                    f"✓ Completed {file_name}"
            }

            message = messages.get(
                action,
                action
            )

            status_box.info(
                message
            )

        try:

            segments = service.process(
                call_id,
                file_path,
                update_progress
            )

            status_box.success(
                f"✓ Module 2 completed — "
                f"{file_name}"
            )

            # =================================================
            # SHOW DIARIZED TRANSCRIPT
            # =================================================

            with st.expander(
                "Timestamped Conversation",
                expanded=True
            ):

                for segment in segments:

                    start = segment["start"]

                    end = segment["end"]

                    speaker = segment["speaker"]

                    text = segment["text"]

                    st.write(
                        f"**{start:.1f}s - "
                        f"{end:.1f}s | "
                        f"{speaker}:** "
                        f"{text}"
                    )

        except Exception as e:

            status_box.error(
                f"❌ Module 2 failed: {e}"
            )