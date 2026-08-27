from datetime import datetime

from database.database import (
    get_connection
)

from module3.sentiment_service import (
    SentimentService
)


class SentimentTool:

    name = "analyze_customer_sentiment"

    description = """
    Analyze sentiment of the customer's conversation.

    Returns sentiment label and sentiment score.

    Use this when sentiment analysis does not already
    exist for the call.
    """

    def __init__(self):

        self.service = SentimentService()

    def run(
        self,
        call_id: str
    ):

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

                "error":
                    "No CUSTOMER transcript found."
            }

        result = (
            self.service.analyze(
                customer_text
            )
        )

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO customer_analysis
                (
                    call_id,
                    sentiment,
                    sentiment_score,
                    created_at
                )

                VALUES (?, ?, ?, ?)

                ON CONFLICT(call_id)
                DO UPDATE SET

                    sentiment =
                        excluded.sentiment,

                    sentiment_score =
                        excluded.sentiment_score,

                    created_at =
                        excluded.created_at
                """,
                (
                    call_id,

                    result[
                        "sentiment"
                    ],

                    result[
                        "score"
                    ],

                    datetime.now()
                    .isoformat()
                )
            )

            conn.commit()

        return {

            "success": True,

            "call_id": call_id,

            "tool": self.name,

            "result": result
        }