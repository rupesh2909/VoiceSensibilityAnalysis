import json

from database.database import (
    get_connection
)


class DashboardService:

    # =====================================================
    # RECOVERY QUEUE
    # =====================================================

    def get_recovery_queue(self):

        with get_connection() as conn:

            rows = conn.execute(
                """
                SELECT

                    c.customer_id,
                    c.customer_name,
                    c.customer_segment,
                    c.customer_value,

                    calls.call_id,
                    calls.file_name,
                    calls.created_at,

                    ca.sentiment,
                    ca.sentiment_score,

                    ce.primary_emotion,
                    ce.emotion_intensity,
                    ce.anger_score,
                    ce.frustration_score,
                    ce.disappointment_score,
                    ce.confidence AS emotion_confidence,

                    rc.dissatisfaction,
                    rc.root_cause_category,
                    rc.root_cause,
                    rc.severity,
                    rc.confidence AS root_cause_confidence,

                    cr.churn_risk_score,
                    cr.churn_risk_level,
                    cr.recovery_priority,
                    cr.customer_intent,
                    cr.closure_intent,
                    cr.fraud_intent,
                    cr.risk_factors,
                    cr.triggered_rules,
                    cr.recommendations

                FROM churn_risk_analysis cr

                INNER JOIN calls
                    ON calls.call_id = cr.call_id

                LEFT JOIN customers c
                    ON c.customer_id =
                       calls.customer_id

                LEFT JOIN customer_analysis ca
                    ON ca.call_id =
                       calls.call_id

                LEFT JOIN customer_emotions ce
                    ON ce.call_id =
                       calls.call_id

                LEFT JOIN dissatisfaction_root_causes rc
                    ON rc.call_id =
                       calls.call_id

                ORDER BY

                    CASE cr.recovery_priority
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'HIGH' THEN 2
                        WHEN 'MEDIUM' THEN 3
                        ELSE 4
                    END,

                    cr.churn_risk_score DESC,

                    calls.created_at DESC
                """
            ).fetchall()

        return [
            self._normalize_row(row)
            for row in rows
        ]

    # =====================================================
    # NORMALIZE
    # =====================================================

    def _normalize_row(
        self,
        row
    ):

        result = dict(row)

        result["risk_factors"] = (
            self._parse_json(
                result.get(
                    "risk_factors"
                ),
                []
            )
        )

        result["triggered_rules"] = (
            self._parse_json(
                result.get(
                    "triggered_rules"
                ),
                []
            )
        )

        result["recommendations"] = (
            self._parse_json(
                result.get(
                    "recommendations"
                ),
                []
            )
        )

        result["closure_intent"] = bool(
            result.get(
                "closure_intent"
            )
        )

        result["fraud_intent"] = bool(
            result.get(
                "fraud_intent"
            )
        )

        return result

    # =====================================================
    # JSON
    # =====================================================

    @staticmethod
    def _parse_json(
        value,
        default
    ):

        if not value:

            return default

        if isinstance(
            value,
            (list, dict)
        ):

            return value

        try:

            return json.loads(
                value
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError
        ):

            return default

    # =====================================================
    # KPI
    # =====================================================

    def get_kpis(self):

        with get_connection() as conn:

            total_customers = conn.execute(
                """
                SELECT COUNT(*)
                FROM customers
                """
            ).fetchone()[0]

            total_calls = conn.execute(
                """
                SELECT COUNT(*)
                FROM calls
                """
            ).fetchone()[0]

            analyzed_calls = conn.execute(
                """
                SELECT COUNT(*)
                FROM churn_risk_analysis
                """
            ).fetchone()[0]

            critical_cases = conn.execute(
                """
                SELECT COUNT(*)
                FROM churn_risk_analysis
                WHERE recovery_priority = 'CRITICAL'
                """
            ).fetchone()[0]

            high_cases = conn.execute(
                """
                SELECT COUNT(*)
                FROM churn_risk_analysis
                WHERE recovery_priority = 'HIGH'
                """
            ).fetchone()[0]

            average_risk = conn.execute(
                """
                SELECT AVG(churn_risk_score)
                FROM churn_risk_analysis
                """
            ).fetchone()[0]

            dissatisfaction_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM dissatisfaction_root_causes
                WHERE dissatisfaction = 'YES'
                """
            ).fetchone()[0]

        return {

            "total_customers":
                total_customers,

            "total_calls":
                total_calls,

            "analyzed_calls":
                analyzed_calls,

            "critical_cases":
                critical_cases,

            "high_cases":
                high_cases,

            "average_risk":
                round(
                    average_risk or 0,
                    1
                ),

            "dissatisfaction_count":
                dissatisfaction_count
        }

    # =====================================================
    # CUSTOMER HISTORY
    # =====================================================

    def get_customer_history(
        self,
        customer_id
    ):

        with get_connection() as conn:

            rows = conn.execute(
                """
                SELECT

                    calls.call_id,
                    calls.file_name,
                    calls.created_at,

                    ca.sentiment,
                    ca.sentiment_score,

                    ce.primary_emotion,
                    ce.emotion_intensity,

                    rc.dissatisfaction,
                    rc.root_cause_category,
                    rc.root_cause,
                    rc.severity,

                    cr.churn_risk_score,
                    cr.churn_risk_level,
                    cr.recovery_priority,
                    cr.closure_intent

                FROM calls

                LEFT JOIN customer_analysis ca
                    ON ca.call_id =
                       calls.call_id

                LEFT JOIN customer_emotions ce
                    ON ce.call_id =
                       calls.call_id

                LEFT JOIN dissatisfaction_root_causes rc
                    ON rc.call_id =
                       calls.call_id

                LEFT JOIN churn_risk_analysis cr
                    ON cr.call_id =
                       calls.call_id

                WHERE calls.customer_id = ?

                ORDER BY calls.created_at DESC
                """,
                (customer_id,)
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =====================================================
    # CUSTOMER PROFILE
    # =====================================================

    def get_customer(
        self,
        customer_id
    ):

        with get_connection() as conn:

            row = conn.execute(
                """
                SELECT
                    customer_id,
                    customer_name,
                    customer_segment,
                    customer_value,
                    created_at
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,)
            ).fetchone()

        if not row:

            return None

        return dict(row)

    # =====================================================
    # REPEATED COMPLAINT
    # =====================================================

    def get_repeated_complaint_count(
        self,
        customer_id,
        root_cause_category
    ):

        if not root_cause_category:

            return 0

        with get_connection() as conn:

            row = conn.execute(
                """
                SELECT COUNT(*)

                FROM calls

                INNER JOIN dissatisfaction_root_causes rc
                    ON rc.call_id = calls.call_id

                WHERE calls.customer_id = ?

                  AND rc.root_cause_category = ?

                  AND rc.dissatisfaction = 'YES'

                  AND datetime(calls.created_at)
                      >= datetime('now', '-30 days')
                """,
                (
                    customer_id,
                    root_cause_category
                )
            ).fetchone()

        return row[0] or 0