import uuid

from datetime import datetime

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
    # GET CALLS PROCESSED BY MODULE 3
    # =====================================================

    def get_calls_for_analysis(self):

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

        customer_text = " ".join(
            row["text"]
            for row in rows
            if row["text"]
        )

        return customer_text

    # =====================================================
    # GET MODULE 3 RESULT
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

            row = conn.execute(
                query,
                (call_id,)
            ).fetchone()

        return row

    # =====================================================
    # PROCESS CALL
    # =====================================================

    def process_call(
        self,
        call_id
    ):

        sentiment = self.get_sentiment(
            call_id
        )

        if not sentiment:

            raise ValueError(
                f"No Module 3 result found "
                f"for {call_id}"
            )

        sentiment_label = (
            sentiment["sentiment"]
        )

        sentiment_score = float(
            sentiment["sentiment_score"]
        )

        # -------------------------------------------------
        # CUSTOMER TEXT ONLY
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
        # NON-NEGATIVE CALL
        # -------------------------------------------------

        if sentiment_label.upper() not in (
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
                customer_text
            )

            return result

        # -------------------------------------------------
        # ROOT CAUSE MODEL
        # -------------------------------------------------

        root_cause_result = (
            self.root_cause_service
            .identify_root_cause(
                customer_text
            )
        )

        # -------------------------------------------------
        # HANDLE MODEL RESULT
        # -------------------------------------------------

        if "category" in root_cause_result:

            category = (
                root_cause_result[
                    "category"
                ]
            )

        elif "root_cause" in root_cause_result:

            category = (
                root_cause_result[
                    "root_cause"
                ]
            )

        elif "labels" in root_cause_result:

            category = (
                root_cause_result[
                    "labels"
                ][0]
            )

        else:

            raise ValueError(
                "Root cause model did not "
                "return a category."
            )

        # -------------------------------------------------

        if "root_cause" in root_cause_result:

            root_cause = (
                root_cause_result[
                    "root_cause"
                ]
            )

        else:

            root_cause = category

        # -------------------------------------------------

        if "confidence" in root_cause_result:

            confidence = float(
                root_cause_result[
                    "confidence"
                ]
            )

        elif "scores" in root_cause_result:

            confidence = float(
                root_cause_result[
                    "scores"
                ][0]
            )

        else:

            raise ValueError(
                "Root cause model did not "
                "return confidence."
            )

        # -------------------------------------------------
        # DISSATISFACTION
        # -------------------------------------------------

        if (
            confidence
            >= ROOT_CAUSE_CONFIDENCE_THRESHOLD
        ):

            dissatisfaction = "YES"

        else:

            dissatisfaction = "UNCERTAIN"

        # -------------------------------------------------
        # SEVERITY
        # -------------------------------------------------

        severity = (
            self._calculate_severity(
                sentiment_score,
                confidence
            )
        )

        result = {

            "call_id":
                call_id,

            "dissatisfaction":
                dissatisfaction,

            "category":
                category,

            "root_cause":
                root_cause,

            "confidence":
                confidence,

            "sentiment":
                sentiment_label,

            "severity":
                severity
        }

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        self.save_result(
            call_id,
            result,
            customer_text
        )

        return result

    # =====================================================
    # SAVE RESULT
    # =====================================================

    def save_result(
        self,
        call_id,
        result,
        customer_text
    ):

        root_cause_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now().isoformat()
        )

        with get_connection() as conn:

            # ---------------------------------------------
            # DELETE PREVIOUS RESULT
            # ---------------------------------------------

            conn.execute(
                """
                DELETE FROM
                    dissatisfaction_root_causes
                WHERE call_id = ?
                """,
                (call_id,)
            )

            # ---------------------------------------------
            # INSERT RESULT
            # ---------------------------------------------

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

                    customer_text,

                    created_at
                )
            )

            conn.commit()

    # =====================================================
    # SEVERITY
    # =====================================================

    def _calculate_severity(
        self,
        sentiment_confidence,
        root_cause_confidence
    ):

        score = (
            sentiment_confidence
            + root_cause_confidence
        ) / 2

        if score >= 0.85:

            return "HIGH"

        if score >= 0.65:

            return "MEDIUM"

        return "LOW"