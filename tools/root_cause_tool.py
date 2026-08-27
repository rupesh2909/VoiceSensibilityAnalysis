import uuid

from datetime import datetime

from database.database import (
    get_connection
)

from module4.root_cause_service import (
    RootCauseService
)


class RootCauseTool:

    name = (
        "identify_dissatisfaction_root_cause"
    )

    description = """
    Analyze the CUSTOMER conversation and identify
    the primary dissatisfaction root cause.

    Use after negative sentiment has been detected.
    """

    def __init__(self):

        self.service = (
            RootCauseService()
        )

    # =====================================================
    # RUN
    # =====================================================

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
                SELECT
                    text

                FROM transcript_segments

                WHERE call_id = ?

                  AND speaker = 'CUSTOMER'

                ORDER BY start_time
                """,
                (call_id,)
            ).fetchall()

        if not rows:

            return {

                "success":
                    False,

                "call_id":
                    call_id,

                "error":
                    (
                        "No CUSTOMER transcript "
                        "found."
                    )
            }

        customer_text = " ".join(

            row["text"]

            for row in rows

            if row["text"]
        )

        if not customer_text.strip():

            return {

                "success":
                    False,

                "call_id":
                    call_id,

                "error":
                    (
                        "CUSTOMER transcript "
                        "is empty."
                    )
            }

        # =================================================
        # QWEN ROOT CAUSE ANALYSIS
        # =================================================

        try:

            result = (
                self.service.analyze(
                    customer_text
                )
            )

        except Exception as e:

            return {

                "success":
                    False,

                "call_id":
                    call_id,

                "error":
                    str(e)
            }

        # =================================================
        # NORMALIZE DISSATISFACTION
        # =================================================

        dissatisfied = bool(
            result.get(
                "dissatisfied",
                False
            )
        )

        dissatisfaction = (
            "YES"
            if dissatisfied
            else "NO"
        )

        # =================================================
        # SAVE
        # =================================================

        root_cause_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now()
            .isoformat()
        )

        try:

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

                        dissatisfaction,

                        result.get(
                            "root_cause_category"
                        ),

                        result.get(
                            "root_cause"
                        ),

                        result.get(
                            "severity"
                        ),

                        result.get(
                            "confidence"
                        ),

                        result.get(
                            "evidence"
                        ),

                        created_at
                    )
                )

                conn.commit()

        except Exception as e:

            return {

                "success":
                    False,

                "call_id":
                    call_id,

                "error":
                    (
                        "Failed to save root cause: "
                        f"{str(e)}"
                    )
            }

        # =================================================
        # RETURN
        # =================================================

        return {

            "success":
                True,

            "call_id":
                call_id,

            "tool":
                self.name,

            "result": {

                **result,

                "dissatisfaction":
                    dissatisfaction
            }
        }