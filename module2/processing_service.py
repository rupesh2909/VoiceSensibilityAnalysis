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
    # DELETE PREVIOUS MODULE 2 RESULT
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
                DELETE FROM transcripts
                WHERE call_id = ?
                """,
                (call_id,)
            )

            conn.commit()

    # =====================================================
    # PROCESS CALL
    # =====================================================

    def process(
        self,
        call_id,
        audio_file,
        progress_callback=None
    ):

        try:

            # -------------------------------------------------
            # Remove old Module 2 results
            # -------------------------------------------------

            self.clear_previous_results(
                call_id
            )

            # -------------------------------------------------
            # Convert audio
            # -------------------------------------------------

            if progress_callback:

                progress_callback(
                    "CONVERTING"
                )

            wav_file = convert_to_wav(
                audio_file
            )

            # -------------------------------------------------
            # Transcription
            # -------------------------------------------------

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

            full_text = result.get(
                "text",
                ""
            )

            language = result.get(
                "language"
            )

            duration = 0.0

            if whisper_segments:

                duration = (
                    whisper_segments[-1]["end"]
                )

            # -------------------------------------------------
            # Save transcription
            # -------------------------------------------------

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

                conn.commit()

            # -------------------------------------------------
            # Diarization
            # -------------------------------------------------

            update_status(
                call_id,
                STATUS_DIARIZING
            )

            if progress_callback:

                progress_callback(
                    "DIARIZING"
                )

                waveform = load_audio_for_pyannote(
                    wav_file
                )

                diarization = (
                    self.diarization_service
                    .diarize(
                        waveform
                    )
                )

            # -------------------------------------------------
            # Align Whisper + diarization
            # -------------------------------------------------

            if progress_callback:

                progress_callback(
                    "ALIGNING"
                )

            aligned_segments = (
                align_segments(
                    whisper_segments,
                    diarization
                )
            )

            # -------------------------------------------------
            # Save diarized segments
            # -------------------------------------------------

            with get_connection() as conn:

                for segment in aligned_segments:

                    conn.execute(
                        """
                        INSERT INTO
                        transcript_segments
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

            # -------------------------------------------------
            # Complete
            # -------------------------------------------------

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