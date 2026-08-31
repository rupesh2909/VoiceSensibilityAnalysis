import json

from database.database import get_connection

from module6.churn_risk_service import (
    ChurnRiskService
)

from module6.retention_rules import (
    evaluate_rules,
    aggregate_recommendations,
    get_highest_priority,
    build_recommendation_decision
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
    # CUSTOMER / HISTORY CONTEXT
    # =====================================================

    def get_customer_context(
        self,
        call_id
    ):
        """
        Retrieve customer profile, current call metadata,
        and 30-day complaint history.
        """

        with get_connection() as conn:

            # ---------------------------------------------
            # Current call + customer
            # ---------------------------------------------

            current = conn.execute(
                """
                SELECT
                    c.call_id,
                    c.customer_id,
                    c.created_at AS call_created_at,
                    cu.customer_name,
                    cu.customer_segment,
                    cu.customer_value,
                    t.duration
                FROM calls c

                LEFT JOIN customers cu
                    ON c.customer_id =
                       cu.customer_id

                LEFT JOIN transcripts t
                    ON c.call_id =
                       t.call_id

                WHERE c.call_id = ?

                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            if not current:
                return None

            customer_id = current[
                "customer_id"
            ]

            # ---------------------------------------------
            # 30-day call history
            # ---------------------------------------------

            history = []

            if customer_id:

                history = conn.execute(
                    """
                    SELECT
                        c.call_id,
                        c.created_at,
                        drc.root_cause_category
                    FROM calls c

                    LEFT JOIN
                        dissatisfaction_root_causes drc
                        ON c.call_id =
                           drc.call_id

                    WHERE c.customer_id = ?

                      AND datetime(c.created_at)
                          >= datetime(
                              'now',
                              '-30 days'
                          )

                    ORDER BY
                        datetime(c.created_at)
                    """,
                    (customer_id,)
                ).fetchall()

            return {
                "customer_id":
                    customer_id,

                "customer_name":
                    current[
                        "customer_name"
                    ],

                "customer_segment":
                    current[
                        "customer_segment"
                    ],

                "customer_value":
                    current[
                        "customer_value"
                    ],

                "call_id":
                    current[
                        "call_id"
                    ],

                "call_created_at":
                    current[
                        "call_created_at"
                    ],

                "call_duration":
                    current[
                        "duration"
                    ],

                "customer_call_count_30d":
                    len(history),

                "previous_root_causes": [
                    row[
                        "root_cause_category"
                    ]
                    for row in history
                    if row[
                        "root_cause_category"
                    ]
                ]
            }        

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
        # CUSTOMER CONTEXT
        # =================================================

        customer_context = (
            self.get_customer_context(
                call_id
            )
        )

        if not customer_context:

            return {
                "success": False,
                "call_id": call_id,
                "tool": self.name,
                "error":
                    "Customer context could not be found."
            }

        # ---------------------------------------------
        # Similar issue
        # ---------------------------------------------

        current_root_cause = (
            root_cause[
                "root_cause_category"
            ]
        )

        previous_root_causes = (
            customer_context[
                "previous_root_causes"
            ]
        )

        similar_issue = False

        if current_root_cause:

            current_category = (
                str(
                    current_root_cause
                )
                .strip()
                .upper()
            )            

            similar_issue = any(
                str(previous).strip().upper()
                ==
                str(current_root_cause).strip().upper()

                for previous
                in previous_root_causes
            )            

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

            anger_score=
                emotion["anger_score"],

            root_cause_category=
                root_cause["root_cause_category"],

            churn_risk_score=
                result["churn_risk_score"],

            customer_value=
                customer_context["customer_value"],

            call_duration=
                customer_context["call_duration"],

            customer_call_count_30d=
                customer_context["customer_call_count_30d"
            ],

            similar_issue=
                similar_issue,

            customer_segment=
                customer_context["customer_segment"]
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
        # RECOMMENDATION DECISION
        # =================================================

        recommendation_decision = (
            build_recommendation_decision(
                triggered_rules,
                churn_risk_score=
                    result["churn_risk_score"],
                sentiment=
                    sentiment["sentiment"]
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
                    recommendation_decision,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))

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

                    recommendation_decision =
                        excluded.recommendation_decision,

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
                    ),
                    json.dumps(
                        recommendation_decision
                    ),
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
                cross_sell_suppression,

            "recommendation_decision":
                recommendation_decision
        }