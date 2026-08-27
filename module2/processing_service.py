import uuid

from datetime import datetime

from database.database import (
    get_connection
)

from config.settings import (
    STATUS_TRANSCRIBING,
    STATUS_DIARIZING,
    STATUS_COMPLETED,
    STATUS_FAILED
)

from module1.call_repository import (
    update_status
)

from .audio_service import (
    convert_to_wav,
    load_audio_for_pyannote
)

from .transcription_service import (
    TranscriptionService
)

from .diarization_service import (
    DiarizationService
)

from .alignment_service import (
    align_segments
)


class ProcessingService:

    def __init__(self):

        self.transcription_service = (
            TranscriptionService()
        )

        self.diarization_service = (
            DiarizationService()
        )

    # =====================================================
    # CLEAR PREVIOUS RESULTS
    # =====================================================

    def clear_previous_results(
        self,
        call_id
    ):

        with get_connection() as conn:

            conn.execute(
                """
                DELETE FROM transcript_segments
                WHERE call_id = ?
                """,
                (call_id,)
            )

            conn.execute(
                """
                DELETE FROM diarization_segments
                WHERE call_id = ?
                """,
                (call_id,)
            )

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

            conn.commit()

    # =====================================================
    # EXTRACT DIARIZATION SEGMENTS
    # =====================================================

    def extract_diarization_segments(
        self,
        diarization
    ):

        segments = []

        for turn, _, speaker in (
            diarization.itertracks(
                yield_label=True
            )
        ):

            segments.append({

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

        return segments

    # =====================================================
    # SAVE DIARIZATION
    # =====================================================

    def save_diarization_segments(
        self,
        call_id,
        segments
    ):

        with get_connection() as conn:

            for segment in segments:

                conn.execute(
                    """
                    INSERT INTO diarization_segments
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

                        segment["start"],

                        segment["end"],

                        segment["speaker"]
                    )
                )

            conn.commit()

    # =====================================================
    # PROCESS
    # =====================================================

    def process(
        self,
        call_id,
        audio_file,
        progress_callback=None
    ):

        try:

            # =================================================
            # CLEAR OLD RESULTS
            # =================================================

            self.clear_previous_results(
                call_id
            )

            # =================================================
            # CONVERT AUDIO
            # =================================================

            if progress_callback:

                progress_callback(
                    "CONVERTING"
                )

            wav_file = convert_to_wav(
                audio_file
            )

            # =================================================
            # TRANSCRIPTION
            # =================================================

            update_status(
                call_id,
                STATUS_TRANSCRIBING
            )

            if progress_callback:

                progress_callback(
                    "TRANSCRIBING"
                )

            result = (
                self.transcription_service
                .transcribe(
                    wav_file
                )
            )

            whisper_segments = (
                result.get(
                    "segments",
                    []
                )
            )

            full_text = (
                result.get(
                    "text",
                    ""
                )
            )

            language = (
                result.get(
                    "language"
                )
            )

            if not whisper_segments:

                raise ValueError(
                    "Whisper returned no segments."
                )

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

            # =================================================
            # SAVE TRANSCRIPT + RAW SEGMENTS
            # =================================================

            transcript_id = str(
                uuid.uuid4()
            )

            with get_connection() as conn:

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

                        datetime.now().isoformat()
                    )
                )

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

            # =================================================
            # DIARIZATION
            # =================================================

            update_status(
                call_id,
                STATUS_DIARIZING
            )

            if progress_callback:

                progress_callback(
                    "DIARIZING"
                )

            waveform = (
                load_audio_for_pyannote(
                    wav_file
                )
            )

            diarization = (
                self.diarization_service
                .diarize(
                    waveform
                )
            )

            diarization_segments = (
                self.extract_diarization_segments(
                    diarization
                )
            )

            if not diarization_segments:

                raise ValueError(
                    "No diarization segments found."
                )

            self.save_diarization_segments(
                call_id,
                diarization_segments
            )

            # =================================================
            # ALIGN
            # =================================================

            if progress_callback:

                progress_callback(
                    "ALIGNING"
                )

            aligned_segments = (
                align_segments(
                    whisper_segments,
                    diarization_segments
                )
            )

            if not aligned_segments:

                raise ValueError(
                    "Alignment returned no segments."
                )

            # =================================================
            # SAVE ALIGNED TRANSCRIPT
            # =================================================

            with get_connection() as conn:

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

                            segment["speaker"],

                            segment["text"]
                        )
                    )

                conn.commit()

            # =================================================
            # COMPLETE
            # =================================================

            update_status(
                call_id,
                STATUS_COMPLETED
            )

            if progress_callback:

                progress_callback(
                    "COMPLETED"
                )

            return aligned_segments

        except Exception:

            update_status(
                call_id,
                STATUS_FAILED
            )

            raise