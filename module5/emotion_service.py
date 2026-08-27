from transformers import pipeline

from config.settings import (
    EMOTION_MODEL,
    MAX_EMOTION_TEXT_LENGTH,
    EMOTION_CONFIDENCE_THRESHOLD,
    EMOTION_LABEL_MAPPING
)


class EmotionService:

    def __init__(self):

        self.model = pipeline(
            "text-classification",
            model=EMOTION_MODEL,
            top_k=None
        )

    # =====================================================
    # ANALYZE CUSTOMER TEXT
    # =====================================================

    def analyze(
        self,
        text
    ):

        if not text or not text.strip():

            raise ValueError(
                "Text cannot be empty."
            )

        # -------------------------------------------------
        # Limit input length
        # -------------------------------------------------

        text = text[
            :MAX_EMOTION_TEXT_LENGTH
        ]

        # -------------------------------------------------
        # Run model
        # -------------------------------------------------

        output = self.model(
            text
        )

        # Depending on transformers version,
        # output can be:
        #
        # [[{...}, {...}]]
        #
        # or
        #
        # [{...}, {...}]
        #

        if (
            output
            and isinstance(
                output[0],
                list
            )
        ):

            output = output[0]

        # -------------------------------------------------
        # Convert model output to dictionary
        # -------------------------------------------------

        scores = {}

        for item in output:

            label = (
                item["label"]
                .lower()
            )

            scores[label] = float(
                item["score"]
            )

        if not scores:

            raise ValueError(
                "Emotion model returned no results."
            )

        # -------------------------------------------------
        # Primary raw emotion
        # -------------------------------------------------

        primary_raw = max(
            scores,
            key=scores.get
        )

        primary_score = scores[
            primary_raw
        ]

        primary_emotion = (
            EMOTION_LABEL_MAPPING.get(
                primary_raw,
                primary_raw.upper()
            )
        )

        # -------------------------------------------------
        # Business scores
        # -------------------------------------------------

        anger_score = scores.get(
            "anger",
            0.0
        )

        frustration_score = scores.get(
            "annoyance",
            0.0
        )

        disappointment_score = scores.get(
            "disappointment",
            0.0
        )

        confusion_score = scores.get(
            "confusion",
            0.0
        )

        fear_score = scores.get(
            "fear",
            0.0
        )

        sadness_score = scores.get(
            "sadness",
            0.0
        )

        neutral_score = scores.get(
            "neutral",
            0.0
        )

        joy_score = scores.get(
            "joy",
            0.0
        )

        surprise_score = scores.get(
            "surprise",
            0.0
        )

        # -------------------------------------------------
        # Customer emotion intensity
        #
        # For the hackathon we define intensity as the
        # strongest negative customer emotion.
        # -------------------------------------------------

        emotion_intensity = max(
            anger_score,
            frustration_score,
            disappointment_score,
            confusion_score
        )

        # -------------------------------------------------
        # Confidence
        # -------------------------------------------------

        confidence = primary_score

        if (
            confidence
            < EMOTION_CONFIDENCE_THRESHOLD
        ):

            primary_emotion = "UNCERTAIN"

        return {

            "primary_emotion":
                primary_emotion,

            "emotion_score":
                primary_score,

            "anger_score":
                anger_score,

            "frustration_score":
                frustration_score,

            "disappointment_score":
                disappointment_score,

            "confusion_score":
                confusion_score,

            "fear_score":
                fear_score,

            "sadness_score":
                sadness_score,

            "neutral_score":
                neutral_score,

            "joy_score":
                joy_score,

            "surprise_score":
                surprise_score,

            "emotion_intensity":
                emotion_intensity,

            "confidence":
                confidence
        }