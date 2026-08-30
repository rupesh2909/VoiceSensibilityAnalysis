import whisper

from config.settings import (
    WHISPER_MODEL,
    WHISPER_FP16
)


# =========================================================
# WHISPER MODEL CACHE
# =========================================================

_whisper_model = None


class TranscriptionService:

    def __init__(self):

        global _whisper_model

        if _whisper_model is None:

            print(
                f"Loading Whisper model: "
                f"{WHISPER_MODEL}"
            )

            _whisper_model = whisper.load_model(
                WHISPER_MODEL,
                device="cuda"
            )

            print(
                "Whisper model loaded."
            )

        else:

            print(
                "Reusing cached Whisper model."
            )

        self.model = _whisper_model

    # =====================================================
    # TRANSCRIBE
    # =====================================================

    def transcribe(
        self,
        audio_file
    ):

        result = self.model.transcribe(
            str(audio_file),
            fp16=WHISPER_FP16
        )

        return result
