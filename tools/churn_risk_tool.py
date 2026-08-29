from database.database import get_connection

from module6.churn_risk_service import (
    ChurnRiskService
)

from module6.retention_rules import (
    evaluate_rules,
    aggregate_recommendations,
    get_highest_priority
)


class ChurnRiskTool:

    name = "analyze_customer_churn_risk"

    description = """
    Calculate customer churn risk and determine
    recovery priority.

    Uses:
        - customer sentiment
        - sentiment score
        - customer emotion
        - frustration / anger / disappointment
        - dissatisfaction
        - root cause severity
        - customer conversation
        - closure intent

    Also evaluates the retention recommendation
    rules and cross-sell suppression rule.

    Requires:
        sentiment
        emotion
        root cause

    Produces:
        churn risk score
        churn risk level
        recovery priority
        risk factors
        triggered retention rules
        recommendations
        cross-sell suppression
    """

    def __init__(self):

        self.service = (
            ChurnRiskService()
        )

    # =====================================================
    # RUN
    # =====================================================

    def run(
        self,
        call_id: str
    ):

        # =================================================
        # GET CUSTOMER TEXT
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
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "No CUSTOMER transcript found."
            }

        customer_text = " ".join(
            row["text"]
            for row in rows
            if row["text"]
        ).strip()

        if not customer_text:

            return {
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "CUSTOMER transcript is empty."
            }

        # =================================================
        # GET SENTIMENT
        # =================================================

        with get_connection() as conn:

            sentiment = conn.execute(
                """
                SELECT
                    sentiment,
                    sentiment_score
                FROM customer_analysis
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

        if not sentiment:

            return {
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "Sentiment analysis is required first."
            }

        # =================================================
        # GET EMOTION
        # =================================================

        with get_connection() as conn:

            emotion = conn.execute(
                """
                SELECT
                    primary_emotion,
                    anger_score,
                    frustration_score,
                    disappointment_score,
                    confusion_score
                FROM customer_emotions
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

        if not emotion:

            return {
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "Emotion analysis is required first."
            }

        # =================================================
        # GET ROOT CAUSE
        # =================================================

        with get_connection() as conn:

            root_cause = conn.execute(
                """
                SELECT
                    dissatisfaction,
                    root_cause_category,
                    severity
                FROM dissatisfaction_root_causes
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

        if not root_cause:

            return {
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "Root cause analysis is required first."
            }

        # =================================================
        # CALCULATE CHURN RISK
        # =================================================

        result = self.service.calculate_score(

            sentiment=
                sentiment["sentiment"],

            sentiment_score=
                sentiment["sentiment_score"],

            primary_emotion=
                emotion["primary_emotion"],

            anger_score=
                emotion["anger_score"],

            frustration_score=
                emotion["frustration_score"],

            disappointment_score=
                emotion["disappointment_score"],

            dissatisfaction=
                root_cause["dissatisfaction"],

            severity=
                root_cause["severity"],

            customer_text=
                customer_text
        )

        # =================================================
        # RETENTION RULES
        # =================================================

        triggered_rules = evaluate_rules(

            customer_text=
                customer_text,

            sentiment=
                sentiment["sentiment"],

            sentiment_score=
                sentiment["sentiment_score"],

            emotion=
                emotion["primary_emotion"],

            frustration_score=
                emotion["frustration_score"],

            root_cause_category=
                root_cause["root_cause_category"],

            churn_risk_score=
                result["churn_risk_score"]
        )

        recommendations = (
            aggregate_recommendations(
                triggered_rules
            )
        )

        recovery_priority = (
            get_highest_priority(
                triggered_rules
            )
        )

        # =================================================
        # CROSS-SELL SUPPRESSION
        # =================================================

        cross_sell_suppression = (

            result["churn_risk_score"] > 75

            and str(
                sentiment["sentiment"]
            ).upper() == "NEGATIVE"
        )

        # =================================================
        # SAVE
        # =================================================

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO churn_risk_analysis
                (
                    call_id,
                    churn_risk_score,
                    churn_risk_level,
                    recovery_priority,
                    closure_intent,
                    risk_factors,
                    score_breakdown,
                    triggered_rules,
                    recommendations,
                    cross_sell_suppression,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))

                ON CONFLICT(call_id)
                DO UPDATE SET

                    churn_risk_score =
                        excluded.churn_risk_score,

                    churn_risk_level =
                        excluded.churn_risk_level,

                    recovery_priority =
                        excluded.recovery_priority,

                    closure_intent =
                        excluded.closure_intent,

                    risk_factors =
                        excluded.risk_factors,

                    score_breakdown =
                        excluded.score_breakdown,

                    triggered_rules =
                        excluded.triggered_rules,

                    recommendations =
                        excluded.recommendations,

                    cross_sell_suppression =
                        excluded.cross_sell_suppression,

                    created_at =
                        excluded.created_at
                """,
                (
                    call_id,

                    result[
                        "churn_risk_score"
                    ],

                    result[
                        "churn_risk_level"
                    ],

                    recovery_priority,

                    int(
                        result[
                            "closure_intent"
                        ]
                    ),

                    str(
                        result[
                            "risk_factors"
                        ]
                    ),

                    str(
                        result[
                            "score_breakdown"
                        ]
                    ),

                    str(
                        triggered_rules
                    ),

                    str(
                        recommendations
                    ),

                    int(
                        cross_sell_suppression
                    )
                )
            )

            conn.commit()

        # =================================================
        # RETURN
        # =================================================

        return {

            "success": True,

            "call_id": call_id,

            "tool": self.name,

            "churn_risk_score":
                result[
                    "churn_risk_score"
                ],

            "churn_risk_level":
                result[
                    "churn_risk_level"
                ],

            "recovery_priority":
                recovery_priority,

            "closure_intent":
                result[
                    "closure_intent"
                ],

            "risk_factors":
                result[
                    "risk_factors"
                ],

            "score_breakdown":
                result[
                    "score_breakdown"
                ],

            "triggered_rules":
                triggered_rules,

            "recommendations":
                recommendations,

            "cross_sell_suppression":
                cross_sell_suppression
        }