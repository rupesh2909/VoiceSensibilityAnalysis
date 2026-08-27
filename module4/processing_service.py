from datetime import datetime
import uuid

from database.database import (
    get_connection
)

from module4.root_cause_service import (
    RootCauseService
)

from config.settings import (
    ROOT_CAUSE_CONFIDENCE_THRESHOLD
)


class RootCauseProcessingService:

    def __init__(self):

        self.root_cause_service = (
            RootCauseService()
        )

    # =====================================================
    # GET CALLS
    # =====================================================

    def get_calls_for_analysis(
        self
    ):

        query = """
            SELECT
                c.call_id,
                c.file_name

            FROM calls c

            INNER JOIN customer_analysis ca
                ON c.call_id = ca.call_id

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
    # GET SENTIMENT
    # =====================================================

    def get_sentiment(
        self,
        call_id
    ):

        query = """
            SELECT
                sentiment,
                sentiment_score

            FROM customer_analysis

            WHERE call_id = ?

            LIMIT 1
        """

        with get_connection() as conn:

            return conn.execute(
                query,
                (call_id,)
            ).fetchone()

    # =====================================================
    # PROCESS
    # =====================================================

    def process_call(
        self,
        call_id
    ):

        sentiment = (
            self.get_sentiment(
                call_id
            )
        )

        if not sentiment:

            raise ValueError(
                f"No Module 3 result found "
                f"for {call_id}"
            )

        sentiment_label = str(
            sentiment["sentiment"]
        ).upper()

        sentiment_score = float(
            sentiment["sentiment_score"]
        )

        # =================================================
        # CUSTOMER TEXT
        # =================================================

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

        # =================================================
        # NON-NEGATIVE CALL
        # =================================================

        if sentiment_label not in (
            "NEGATIVE",
            "DISSATISFIED"
        ):

            result = {

                "call_id":
                    call_id,

                "dissatisfaction":
                    "NO",

                "category":
                    "Not applicable",

                "root_cause":
                    "Not applicable",

                "confidence":
                    1.0,

                "sentiment":
                    sentiment_label,

                "severity":
                    "LOW"
            }

            self.save_result(
                call_id,
                result,
                "No dissatisfaction detected."
            )

            return result

        # =================================================
        # QWEN ROOT CAUSE
        # =================================================

        analysis = (
            self.root_cause_service
            .analyze(
                customer_text
            )
        )

        # =================================================
        # NORMALIZE
        # =================================================

        confidence = float(
            analysis.get(
                "confidence",
                0.0
            )
        )

        if not analysis.get(
            "dissatisfied",
            False
        ):

            dissatisfaction = "NO"

        elif (
            confidence
            >= ROOT_CAUSE_CONFIDENCE_THRESHOLD
        ):

            dissatisfaction = "YES"

        else:

            dissatisfaction = "UNCERTAIN"

        result = {

            "call_id":
                call_id,

            "dissatisfaction":
                dissatisfaction,

            "category":
                analysis.get(
                    "root_cause_category",
                    "Other"
                ),

            "root_cause":
                analysis.get(
                    "root_cause",
                    ""
                ),

            "confidence":
                confidence,

            "sentiment":
                sentiment_label,

            "severity":
                analysis.get(
                    "severity",
                    "MEDIUM"
                ),

            "evidence":
                analysis.get(
                    "evidence",
                    ""
                )
        }

        # =================================================
        # SAVE
        # =================================================

        self.save_result(
            call_id,
            result,
            result["evidence"]
        )

        return result

    # =====================================================
    # SAVE
    # =====================================================

    def save_result(
        self,
        call_id,
        result,
        evidence
    ):

        root_cause_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now()
            .isoformat()
        )

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO
                dissatisfaction_root_causes
                (
                    root_cause_id,
                    call_id,
                    dissatisfaction,
                    root_cause_category,
                    root_cause,
                    severity,
                    confidence,
                    evidence,
                    created_at
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(call_id)
                DO UPDATE SET

                    dissatisfaction =
                        excluded.dissatisfaction,

                    root_cause_category =
                        excluded.root_cause_category,

                    root_cause =
                        excluded.root_cause,

                    severity =
                        excluded.severity,

                    confidence =
                        excluded.confidence,

                    evidence =
                        excluded.evidence,

                    created_at =
                        excluded.created_at
                """,
                (
                    root_cause_id,

                    call_id,

                    result[
                        "dissatisfaction"
                    ],

                    result[
                        "category"
                    ],

                    result[
                        "root_cause"
                    ],

                    result[
                        "severity"
                    ],

                    result[
                        "confidence"
                    ],

                    evidence,

                    created_at
                )
            )

            conn.commit()