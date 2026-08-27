import uuid

from datetime import datetime

from database.database import (
    get_connection
)

from module5.emotion_service import (
    EmotionService
)


class EmotionTool:

    name = "analyze_customer_emotion"

    description = """
    Analyze the customer's emotional state from the
    customer-only transcript.

    Use this tool when:
    - customer emotion is unknown
    - anger/frustration/disappointment/confusion
      needs to be detected
    - customer prioritization requires emotional signals
    - sentiment alone is insufficient

    Do not call this tool if emotion analysis already
    exists for the call unless a re-analysis is explicitly
    requested.
    """

    def __init__(self):

        self.service = EmotionService()

    def run(
        self,
        call_id: str
    ):

        # =================================================
        # GET CUSTOMER TRANSCRIPT
        # =================================================

        with get_connection() as conn:

            rows = conn.execute(
                """
                SELECT text

                FROM transcript_segments

                WHERE call_id = ?

                  AND speaker = 'CUSTOMER'

                ORDER BY start_time
                """,
                (call_id,)
            ).fetchall()

        customer_text = " ".join(
            row["text"]
            for row in rows
            if row["text"]
        )

        if not customer_text.strip():

            return {
                "success": False,

                "call_id": call_id,

                "error":
                    "No CUSTOMER transcript found."
            }

        # =================================================
        # ANALYZE
        # =================================================

        result = (
            self.service.analyze(
                customer_text
            )
        )

        # =================================================
        # SAVE
        # =================================================

        emotion_id = str(
            uuid.uuid4()
        )

        now = (
            datetime.now()
            .isoformat()
        )

        with get_connection() as conn:

            # Idempotent
            conn.execute(
                """
                INSERT INTO customer_emotions
                (
                    emotion_id,
                    call_id,

                    primary_emotion,
                    emotion_score,

                    anger_score,
                    frustration_score,
                    disappointment_score,
                    confusion_score,

                    fear_score,
                    sadness_score,
                    neutral_score,
                    joy_score,
                    surprise_score,

                    emotion_intensity,
                    confidence,

                    evidence,
                    created_at
                )

                VALUES
                (
                    ?, ?,

                    ?, ?,

                    ?, ?, ?, ?,

                    ?, ?, ?, ?, ?,

                    ?, ?,

                    ?, ?
                )

                ON CONFLICT(call_id)
                DO UPDATE SET

                    primary_emotion =
                        excluded.primary_emotion,

                    emotion_score =
                        excluded.emotion_score,

                    anger_score =
                        excluded.anger_score,

                    frustration_score =
                        excluded.frustration_score,

                    disappointment_score =
                        excluded.disappointment_score,

                    confusion_score =
                        excluded.confusion_score,

                    fear_score =
                        excluded.fear_score,

                    sadness_score =
                        excluded.sadness_score,

                    neutral_score =
                        excluded.neutral_score,

                    joy_score =
                        excluded.joy_score,

                    surprise_score =
                        excluded.surprise_score,

                    emotion_intensity =
                        excluded.emotion_intensity,

                    confidence =
                        excluded.confidence,

                    evidence =
                        excluded.evidence,

                    created_at =
                        excluded.created_at
                """,
                (
                    emotion_id,
                    call_id,

                    result[
                        "primary_emotion"
                    ],

                    result[
                        "emotion_score"
                    ],

                    result[
                        "anger_score"
                    ],

                    result[
                        "frustration_score"
                    ],

                    result[
                        "disappointment_score"
                    ],

                    result[
                        "confusion_score"
                    ],

                    result[
                        "fear_score"
                    ],

                    result[
                        "sadness_score"
                    ],

                    result[
                        "neutral_score"
                    ],

                    result[
                        "joy_score"
                    ],

                    result[
                        "surprise_score"
                    ],

                    result[
                        "emotion_intensity"
                    ],

                    result[
                        "confidence"
                    ],

                    customer_text,

                    now
                )
            )

            conn.commit()

        return {

            "success": True,

            "call_id": call_id,

            "tool": self.name,

            "result": result
        }