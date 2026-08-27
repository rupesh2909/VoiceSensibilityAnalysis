import uuid

from datetime import datetime

from database.database import (
    get_connection
)

from module2.transcription_service import (
    TranscriptionService
)


class TranscriptionTool:

    name = "transcribe_call"

    description = """
    Transcribe the audio recording associated with a call.

    The tool stores:
        1. Full transcription
        2. Timestamped Whisper segments

    Input:
        call_id
    """

    def __init__(self):

        self.service = (
            TranscriptionService()
        )

    # =====================================================
    # RUN
    # =====================================================

    def run(
        self,
        call_id: str
    ):

        # =================================================
        # GET CALL
        # =================================================

        with get_connection() as conn:

            call = conn.execute(
                """
                SELECT
                    call_id,
                    file_path,
                    file_name
                FROM calls
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

        if not call:

            return {
                "success": False,
                "call_id": call_id,
                "error": "Call not found."
            }

        # =================================================
        # CHECK EXISTING TRANSCRIPTION
        # =================================================

        with get_connection() as conn:

            transcript = conn.execute(
                """
                SELECT
                    transcript_id,
                    full_text,
                    language,
                    duration
                FROM transcripts
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            raw_segment_count = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM transcript_raw_segments
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

        # -------------------------------------------------
        # Only consider transcription complete when BOTH
        # full transcript and timestamped segments exist.
        # -------------------------------------------------

        if (
            transcript
            and raw_segment_count["count"] > 0
        ):

            return {

                "success": True,

                "call_id":
                    call_id,

                "tool":
                    self.name,

                "already_exists":
                    True,

                "result":
                    dict(transcript),

                "segments_created":
                    raw_segment_count["count"]
            }

        # =================================================
        # RUN WHISPER
        # =================================================

        try:

            result = (
                self.service.transcribe(
                    call["file_path"]
                )
            )

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "tool":
                    self.name,

                "error":
                    str(e)
            }

        # =================================================
        # EXTRACT RESULTS
        # =================================================

        full_text = result.get(
            "text",
            ""
        )

        language = result.get(
            "language",
            "unknown"
        )

        whisper_segments = (
            result.get(
                "segments",
                []
            )
        )

        # -------------------------------------------------
        # Duration
        # -------------------------------------------------

        duration = result.get(
            "duration"
        )

        if (
            duration is None
            and whisper_segments
        ):

            duration = max(
                float(
                    segment.get(
                        "end",
                        0.0
                    )
                )

                for segment
                in whisper_segments
            )

        # -------------------------------------------------
        # Alignment requires timestamped segments.
        # -------------------------------------------------

        if not whisper_segments:

            return {

                "success": False,

                "call_id":
                    call_id,

                "tool":
                    self.name,

                "error":
                    (
                        "Whisper returned no timestamped "
                        "segments. Alignment cannot proceed."
                    )
            }

        # =================================================
        # SAVE
        # =================================================

        transcript_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now().isoformat()
        )

        try:

            with get_connection() as conn:

                # -----------------------------------------
                # Clear previous partial results
                # -----------------------------------------

                conn.execute(
                    """
                    DELETE FROM transcript_raw_segments
                    WHERE call_id = ?
                    """,
                    (call_id,)
                )

                conn.execute(
                    """
                    DELETE FROM transcripts
                    WHERE call_id = ?
                    """,
                    (call_id,)
                )

                # -----------------------------------------
                # Save full transcript
                # -----------------------------------------

                conn.execute(
                    """
                    INSERT INTO transcripts
                    (
                        transcript_id,
                        call_id,
                        language,
                        duration,
                        full_text,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transcript_id,
                        call_id,
                        language,
                        duration,
                        full_text,
                        created_at
                    )
                )

                # -----------------------------------------
                # Save Whisper raw segments
                # -----------------------------------------

                for segment in whisper_segments:

                    conn.execute(
                        """
                        INSERT INTO transcript_raw_segments
                        (
                            call_id,
                            start_time,
                            end_time,
                            text
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            call_id,

                            float(
                                segment.get(
                                    "start",
                                    0.0
                                )
                            ),

                            float(
                                segment.get(
                                    "end",
                                    0.0
                                )
                            ),

                            str(
                                segment.get(
                                    "text",
                                    ""
                                )
                            ).strip()
                        )
                    )

                conn.commit()

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "tool":
                    self.name,

                "error":
                    (
                        "Failed to save transcription: "
                        f"{str(e)}"
                    )
            }

        # =================================================
        # RETURN
        # =================================================

        return {

            "success": True,

            "call_id":
                call_id,

            "tool":
                self.name,

            "already_exists":
                False,

            "segments_created":
                len(
                    whisper_segments
                ),

            "result": {

                "transcript_id":
                    transcript_id,

                "language":
                    language,

                "duration":
                    duration,

                "text":
                    full_text
            }
        }