import uuid

from datetime import datetime

from database.database import (
    get_connection
)

from module5.emotion_service import (
    EmotionService
)


class EmotionProcessingService:

    def __init__(self):

        self.emotion_service = (
            EmotionService()
        )

    # =====================================================
    # GET CALLS AVAILABLE FOR MODULE 5
    # =====================================================

    def get_calls_for_analysis(self):

        query = """
            SELECT DISTINCT
                c.call_id,
                c.file_name
            FROM calls c

            INNER JOIN transcript_segments ts
                ON c.call_id = ts.call_id

            WHERE EXISTS
            (
                SELECT 1
                FROM transcript_segments customer_ts
                WHERE customer_ts.call_id = c.call_id
                  AND customer_ts.speaker = 'CUSTOMER'
            )

            ORDER BY c.created_at DESC
        """

        with get_connection() as conn:

            return conn.execute(
                query
            ).fetchall()

    # =====================================================
    # GET CUSTOMER TEXT
    # =====================================================

    def get_customer_text(
        self,
        call_id
    ):

        query = """
            SELECT
                text
            FROM transcript_segments
            WHERE call_id = ?
              AND speaker = 'CUSTOMER'
            ORDER BY start_time
        """

        with get_connection() as conn:

            rows = conn.execute(
                query,
                (call_id,)
            ).fetchall()

        return " ".join(
            row["text"]
            for row in rows
            if row["text"]
        )

    # =====================================================
    # DELETE PREVIOUS RESULT
    # =====================================================

    def clear_previous_result(
        self,
        call_id
    ):

        with get_connection() as conn:

            conn.execute(
                """
                DELETE FROM customer_emotions
                WHERE call_id = ?
                """,
                (call_id,)
            )

            conn.commit()

    # =====================================================
    # SAVE RESULT
    # =====================================================

    def save_result(
        self,
        call_id,
        result,
        customer_text
    ):

        emotion_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now().isoformat()
        )

        with get_connection() as conn:

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

                    created_at
                )
            )

            conn.commit()

    # =====================================================
    # PROCESS CALL
    # =====================================================

    def process_call(
        self,
        call_id
    ):

        # -------------------------------------------------
        # Get CUSTOMER conversation
        # -------------------------------------------------

        customer_text = (
            self.get_customer_text(
                call_id
            )
        )

        if not customer_text.strip():

            raise ValueError(
                f"No CUSTOMER text found "
                f"for {call_id}"
            )

        # -------------------------------------------------
        # Run emotion model
        # -------------------------------------------------

        result = (
            self.emotion_service
            .analyze(
                customer_text
            )
        )

        result["call_id"] = (
            call_id
        )

        # -------------------------------------------------
        # Replace previous result
        # -------------------------------------------------

        self.clear_previous_result(
            call_id
        )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        self.save_result(
            call_id,
            result,
            customer_text
        )

        return result