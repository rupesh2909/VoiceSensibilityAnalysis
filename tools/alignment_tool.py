from database.database import (
    get_connection
)

from module2.alignment_service import (
    align_segments
)


class AlignmentTool:

    name = (
        "align_transcript_with_speakers"
    )

    description = """
    Align Whisper transcription segments with
    diarization segments to create a
    speaker-labelled transcript.

    Requires:
        transcript_raw_segments
        diarization_segments

    Produces:
        transcript_segments
    """

    def run(
        self,
        call_id: str
    ):

        # =================================================
        # GET WHISPER SEGMENTS
        # =================================================

        with get_connection() as conn:

            raw_rows = conn.execute(
                """
                SELECT
                    start_time,
                    end_time,
                    text

                FROM transcript_raw_segments

                WHERE call_id = ?

                ORDER BY start_time
                """,
                (call_id,)
            ).fetchall()

        if not raw_rows:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "No transcription segments found. "
                        "Run transcription first."
                    )
            }

        # =================================================
        # GET DIARIZATION SEGMENTS
        # =================================================

        with get_connection() as conn:

            diarization_rows = conn.execute(
                """
                SELECT
                    start_time,
                    end_time,
                    speaker

                FROM diarization_segments

                WHERE call_id = ?

                ORDER BY start_time
                """,
                (call_id,)
            ).fetchall()

        if not diarization_rows:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "No diarization segments found. "
                        "Run diarization first."
                    )
            }

        # =================================================
        # CONVERT DB ROWS
        # =================================================

        whisper_segments = [

            {
                "start":
                    float(
                        row["start_time"]
                    ),

                "end":
                    float(
                        row["end_time"]
                    ),

                "text":
                    row["text"] or ""
            }

            for row in raw_rows
        ]

        diarization_segments = [

            {
                "start":
                    float(
                        row["start_time"]
                    ),

                "end":
                    float(
                        row["end_time"]
                    ),

                "speaker":
                    row["speaker"]
            }

            for row in diarization_rows
        ]

        # =================================================
        # ALIGN
        # =================================================

        try:

            aligned_segments = (
                align_segments(
                    whisper_segments,
                    diarization_segments
                )
            )

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Alignment failed: "
                        f"{str(e)}"
                    )
            }

        if not aligned_segments:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    "Alignment returned no segments."
            }

        # =================================================
        # SAVE
        # =================================================

        try:

            with get_connection() as conn:

                conn.execute(
                    """
                    DELETE FROM transcript_segments
                    WHERE call_id = ?
                    """,
                    (call_id,)
                )

                for segment in aligned_segments:

                    conn.execute(
                        """
                        INSERT INTO transcript_segments
                        (
                            call_id,
                            start_time,
                            end_time,
                            speaker,
                            text
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            call_id,

                            segment["start"],

                            segment["end"],

                            segment.get(
                                "speaker",
                                "UNKNOWN"
                            ),

                            segment.get(
                                "text",
                                ""
                            )
                        )
                    )

                conn.commit()

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Failed to save aligned "
                        f"segments: {str(e)}"
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

            "segments_created":
                len(
                    aligned_segments
                )
        }