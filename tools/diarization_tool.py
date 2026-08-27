from database.database import get_connection

from module2.audio_service import (
    convert_to_wav,
    load_audio_for_pyannote
)

from module2.diarization_service import (
    DiarizationService
)


class DiarizationTool:

    name = "diarize_call"

    description = """
    Perform speaker diarization on a call recording.

    This tool identifies speaker segments and stores
    start time, end time and speaker information in
    the diarization_segments table.

    Input:
        call_id

    Output:
        Number of diarization segments created.
    """

    def __init__(self):

        self.service = (
            DiarizationService()
        )

    # =====================================================
    # MAIN TOOL METHOD
    # =====================================================

    def run(
        self,
        call_id
    ):

        # -------------------------------------------------
        # 1. GET CALL INFORMATION
        # -------------------------------------------------

        with get_connection() as conn:

            call = conn.execute(
                """
                SELECT
                    call_id,
                    file_path

                FROM calls

                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

        # -------------------------------------------------
        # Call doesn't exist
        # -------------------------------------------------

        if not call:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    "Call not found in database."
            }

        # -------------------------------------------------
        # Audio path missing
        # -------------------------------------------------

        file_path = call["file_path"]

        if not file_path:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    "No audio file path found for call."
            }

        # =================================================
        # 2. CONVERT AUDIO TO WAV
        # =================================================

        try:

            wav_file = convert_to_wav(
                file_path
            )

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Audio conversion failed: "
                        f"{str(e)}"
                    )
            }

        # =================================================
        # 3. LOAD AUDIO FOR PYANNOTE
        # =================================================

        try:

            waveform = (
                load_audio_for_pyannote(
                    wav_file
                )
            )

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Unable to load audio "
                        f"for diarization: {str(e)}"
                    )
            }

        # =================================================
        # 4. RUN DIARIZATION
        # =================================================

        try:

            diarization_result = (
                self.service.diarize(
                    waveform
                )
            )

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Diarization failed: "
                        f"{str(e)}"
                    )
            }

        # =================================================
        # 5. VALIDATE RESULT
        # =================================================

        if diarization_result is None:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    "Diarization returned no result."
            }

        # =================================================
        # 6. EXTRACT PYANNOTE SEGMENTS
        # =================================================

        diarization_segments = []

        try:

            for turn, _, speaker in (
                diarization_result
                .itertracks(
                    yield_label=True
                )
            ):

                diarization_segments.append({

                    "start":
                        float(
                            turn.start
                        ),

                    "end":
                        float(
                            turn.end
                        ),

                    "speaker":
                        str(
                            speaker
                        )
                })

        except Exception as e:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Unable to parse "
                        f"diarization result: {str(e)}"
                    )
            }

        # =================================================
        # 7. CHECK WHETHER SEGMENTS EXIST
        # =================================================

        if not diarization_segments:

            return {

                "success": False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Diarization completed but "
                        "no speaker segments were found."
                    )
            }

        # =================================================
        # 8. SAVE TO DATABASE
        # =================================================

        try:

            with get_connection() as conn:

                # -----------------------------------------
                # Remove previous diarization
                # -----------------------------------------

                conn.execute(
                    """
                    DELETE FROM diarization_segments

                    WHERE call_id = ?
                    """,
                    (call_id,)
                )

                # -----------------------------------------
                # Insert new diarization segments
                # -----------------------------------------

                for segment in (
                    diarization_segments
                ):

                    conn.execute(
                        """
                        INSERT INTO
                        diarization_segments
                        (
                            call_id,
                            start_time,
                            end_time,
                            speaker
                        )

                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            call_id,

                            segment[
                                "start"
                            ],

                            segment[
                                "end"
                            ],

                            segment[
                                "speaker"
                            ]
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
                        "Failed to save diarization "
                        f"results: {str(e)}"
                    )
            }

        # =================================================
        # 9. CALCULATE SPEAKER COUNT
        # =================================================

        unique_speakers = set(

            segment[
                "speaker"
            ]

            for segment
            in diarization_segments
        )

        # =================================================
        # 10. RETURN TOOL RESULT
        # =================================================

        return {

            "success": True,

            "call_id":
                call_id,

            "tool":
                self.name,

            "segments_created":
                len(
                    diarization_segments
                ),

            "speaker_count":
                len(
                    unique_speakers
                ),

            "speakers":
                sorted(
                    unique_speakers
                )
        }