import os

from config.settings import (
    DIARIZATION_MODEL,
    MIN_SPEAKERS,
    MAX_SPEAKERS,
    AUDIO_SAMPLE_RATE
)


class DiarizationService:

    def __init__(self):

        token = os.getenv(
            "HF_TOKEN"
        )

        if not token:

            raise ValueError(
                "HF_TOKEN is not configured "
                "in .env"
            )

        print(
            "Loading diarization model..."
        )

        # -------------------------------------------------
        # Lazy import
        # -------------------------------------------------

        try:

            from pyannote.audio import (
                Pipeline
            )

        except Exception as e:

            raise RuntimeError(
                "Unable to import pyannote.audio.\n\n"
                "Make sure Module 2 dependencies "
                "are installed in the active "
                "virtual environment.\n\n"
                f"Original error: {e}"
            ) from e

        # -------------------------------------------------
        # Load model
        # -------------------------------------------------

        self.pipeline = (
            Pipeline.from_pretrained(
                DIARIZATION_MODEL,
                token=token
            )
        )

        if self.pipeline is None:

            raise RuntimeError(
                "PyAnnote pipeline could not "
                "be loaded."
            )

        print(
            "Diarization model loaded."
        )

    def diarize(
        self,
        waveform
    ):

        audio = {
            "waveform": waveform,
            "sample_rate":
                AUDIO_SAMPLE_RATE
        }

        output = self.pipeline(
            audio,
            min_speakers=MIN_SPEAKERS,
            max_speakers=MAX_SPEAKERS
        )

        return (
            output.exclusive_speaker_diarization
        )