import json
import uuid

from datetime import datetime

from database.database import (
    get_connection
)

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
    Calculate customer churn risk using existing
    sentiment, emotion, dissatisfaction, root cause
    and customer conversation data.

    Also evaluates the MVP retention rules and
    generates recovery recommendations.

    Requires:
        sentiment
        emotion
        root cause
        aligned customer transcript
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
        # GET EXISTING ANALYSIS
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

            emotion = conn.execute(
                """
                SELECT
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
                    confidence
                FROM customer_emotions
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            root_cause = conn.execute(
                """
                SELECT
                    dissatisfaction,
                    root_cause_category,
                    root_cause,
                    severity,
                    confidence,
                    evidence
                FROM dissatisfaction_root_causes
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            transcript_rows = conn.execute(
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

            call = conn.execute(
                """
                SELECT
                    call_id,
                    file_name
                FROM calls
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

        # =================================================
        # VALIDATE CALL
        # =================================================

        if not call:

            return {
                "success": False,
                "call_id": call_id,
                "error": "Call not found."
            }

        # =================================================
        # VALIDATE REQUIRED ANALYSIS
        # =================================================

        if not sentiment:

            return {
                "success": False,
                "call_id": call_id,
                "error": (
                    "Sentiment analysis is missing. "
                    "Run Module 3 first."
                )
            }

        if not emotion:

            return {
                "success": False,
                "call_id": call_id,
                "error": (
                    "Emotion analysis is missing. "
                    "Run Module 5 first."
                )
            }

        if not root_cause:

            return {
                "success": False,
                "call_id": call_id,
                "error": (
                    "Root cause analysis is missing. "
                    "Run Module 4 first."
                )
            }

        if not transcript_rows:

            return {
                "success": False,
                "call_id": call_id,
                "error": (
                    "No CUSTOMER transcript found."
                )
            }

        # =================================================
        # CUSTOMER TEXT
        # =================================================

        customer_text = " ".join(

            row["text"]

            for row in transcript_rows

            if row["text"]
        )

        # =================================================
        # CALCULATE CHURN SCORE
        # =================================================

        result = (
            self.service.calculate_score(

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
        )

        churn_score = (
            result["churn_risk_score"]
        )

        # =================================================
        # EVALUATE RETENTION RULES
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
                churn_score
        )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

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

        # -------------------------------------------------
        # Rule 10 is a business rule and should influence
        # recommendations but not recovery priority.
        # -------------------------------------------------

        business_rule_triggered = any(

            rule.get("rule_id")
            == "RULE_10"

            for rule
            in triggered_rules
        )

        # =================================================
        # SAVE
        # =================================================

        churn_analysis_id = str(
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
                    INSERT INTO churn_risk_analysis
                    (
                        churn_analysis_id,
                        call_id,
                        churn_risk_score,
                        churn_risk_level,
                        recovery_priority,
                        customer_intent,
                        closure_intent,
                        fraud_intent,
                        risk_factors,
                        triggered_rules,
                        recommendations,
                        created_at
                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(call_id)
                    DO UPDATE SET

                        churn_risk_score =
                            excluded.churn_risk_score,

                        churn_risk_level =
                            excluded.churn_risk_level,

                        recovery_priority =
                            excluded.recovery_priority,

                        customer_intent =
                            excluded.customer_intent,

                        closure_intent =
                            excluded.closure_intent,

                        fraud_intent =
                            excluded.fraud_intent,

                        risk_factors =
                            excluded.risk_factors,

                        triggered_rules =
                            excluded.triggered_rules,

                        recommendations =
                            excluded.recommendations,

                        created_at =
                            excluded.created_at
                    """,
                    (
                        churn_analysis_id,

                        call_id,

                        churn_score,

                        result[
                            "churn_risk_level"
                        ],

                        recovery_priority,

                        (
                            "Product Closure Intent"
                            if result[
                                "closure_intent"
                            ]
                            else "Complaint / Service Issue"
                        ),

                        int(
                            result[
                                "closure_intent"
                            ]
                        ),

                        int(
                            any(
                                rule.get(
                                    "rule_id"
                                ) == "RULE_2"

                                for rule
                                in triggered_rules
                            )
                        ),

                        json.dumps(
                            result[
                                "risk_factors"
                            ]
                        ),

                        json.dumps(
                            triggered_rules
                        ),

                        json.dumps(
                            recommendations
                        ),

                        created_at
                    )
                )

                conn.commit()

        except Exception as e:

            return {
                "success": False,
                "call_id": call_id,
                "error": (
                    "Failed to save churn "
                    f"analysis: {str(e)}"
                )
            }

        # =================================================
        # RETURN
        # =================================================

        return {

            "success": True,

            "call_id":
                call_id,

            "tool":
                self.name,

            "churn_risk_score":
                churn_score,

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
                business_rule_triggered
        }