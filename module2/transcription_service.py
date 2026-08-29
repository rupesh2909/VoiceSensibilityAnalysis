import whisper

from config.settings import (
    WHISPER_MODEL,
    WHISPER_FP16
)


class TranscriptionService:

    def __init__(self):

        print(
            f"Loading Whisper model: "
            f"{WHISPER_MODEL}"
        )

        self.model = whisper.load_model(
            WHISPER_MODEL,
            device="cuda"
        )

        print(
            "Whisper model loaded."
        )

    def transcribe(
        self,
        audio_file
    ):

        result = self.model.transcribe(
            str(audio_file),
            fp16=WHISPER_FP16
        )

        return result