from transformers import pipeline

from config.settings import (
    SENTIMENT_MODEL,
    MAX_SENTIMENT_TEXT_LENGTH
)


class SentimentService:

    def __init__(self):

        print(
            f"Loading sentiment model: "
            f"{SENTIMENT_MODEL}"
        )

        self.model = pipeline(
            "sentiment-analysis",
            model=SENTIMENT_MODEL
        )

        print(
            "Sentiment model loaded."
        )

    def analyze(
        self,
        text
    ):

        if not text.strip():

            return {
                "sentiment": "UNKNOWN",
                "score": 0.0
            }

        text = text[
            :MAX_SENTIMENT_TEXT_LENGTH
        ]

        result = self.model(
            text
        )[0]

        return {
            "sentiment": result["label"],
            "score": result["score"]
        }