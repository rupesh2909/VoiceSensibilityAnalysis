import sys
import json
from pathlib import Path


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from database.database import (
    get_connection
)


# =========================================================
# DISPLAY HELPERS
# =========================================================

def section(title):

    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def field(label, value):

    if value is None:
        value = "N/A"

    print(
        f"{label:<25}: {value}"
    )


def parse_json(value):

    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError
    ):
        return value


def print_json_field(
    label,
    value
):

    parsed = parse_json(value)

    if isinstance(
        parsed,
        (dict, list)
    ):

        print()
        print(
            f"{label}:"
        )

        print(
            json.dumps(
                parsed,
                indent=2,
                ensure_ascii=False
            )
        )

    else:

        field(
            label,
            parsed
        )


# =========================================================
# MAIN
# =========================================================

def inspect_call(call_id):

    with get_connection() as conn:

        # =================================================
        # CALL
        # =================================================

        call = conn.execute(
            """
            SELECT *
            FROM calls
            WHERE call_id = ?
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if not call:

            print()
            print("=" * 75)
            print(
                f"CALL NOT FOUND: {call_id}"
            )
            print("=" * 75)

            return 1

        # =================================================
        # CUSTOMER
        # =================================================

        customer = conn.execute(
            """
            SELECT *
            FROM customers
            WHERE customer_id = ?
            LIMIT 1
            """,
            (call["customer_id"],)
        ).fetchone()

        # =================================================
        # CALL INFORMATION
        # =================================================

        section(
            f"CALL ANALYSIS: {call_id}"
        )

        section(
            "[1] CALL INFORMATION"
        )

        field(
            "Call ID",
            call["call_id"]
        )

        field(
            "Customer ID",
            call["customer_id"]
        )

        field(
            "File Name",
            call["file_name"]
        )

        field(
            "Source",
            call["source"]
        )

        field(
            "Status",
            call["status"]
        )

        field(
            "Created At",
            call["created_at"]
        )

        if customer:

            print()

            field(
                "Customer Name",
                customer["customer_name"]
            )

            field(
                "Customer Segment",
                customer["customer_segment"]
            )

            field(
                "Customer Value",
                customer["customer_value"]
            )

        # =================================================
        # TRANSCRIPT
        # =================================================

        section(
            "[2] TRANSCRIPTION"
        )

        transcript = conn.execute(
            """
            SELECT *
            FROM transcripts
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if transcript:

            field(
                "Language",
                transcript["language"]
            )

            field(
                "Duration",
                transcript["duration"]
            )

            print()

            print(
                "Full Text:"
            )

            print(
                transcript["full_text"]
                or "N/A"
            )

        else:

            print(
                "Transcript not available."
            )

        # =================================================
        # RAW TRANSCRIPTION SEGMENTS
        # =================================================

        section(
            "[3] RAW TRANSCRIPTION SEGMENTS"
        )

        raw_segments = conn.execute(
            """
            SELECT
                start_time,
                end_time,
                text
            FROM transcript_raw_segments
            WHERE call_id = ?
            ORDER BY start_time
            """,
            (call_id,)
        ).fetchall()

        if raw_segments:

            for row in raw_segments:

                print(
                    f"{row['start_time']:>8.2f} - "
                    f"{row['end_time']:>8.2f} | "
                    f"{row['text']}"
                )

        else:

            print(
                "Raw transcription segments not available."
            )

        # =================================================
        # DIARIZATION
        # =================================================

        section(
            "[4] DIARIZATION"
        )

        diarization = conn.execute(
            """
            SELECT
                start_time,
                end_time,
                speaker
            FROM diarization_segments
            WHERE call_id = ?
            ORDER BY start_time
            """,
            (call_id,)
        ).fetchall()

        if diarization:

            for row in diarization:

                print(
                    f"{row['start_time']:>8.2f} - "
                    f"{row['end_time']:>8.2f} | "
                    f"{row['speaker']}"
                )

        else:

            print(
                "Diarization data not available."
            )

        # =================================================
        # ALIGNED TRANSCRIPT
        # =================================================

        section(
            "[5] ALIGNED CONVERSATION"
        )

        aligned = conn.execute(
            """
            SELECT
                start_time,
                end_time,
                speaker,
                text
            FROM transcript_segments
            WHERE call_id = ?
            ORDER BY start_time
            """,
            (call_id,)
        ).fetchall()

        if aligned:

            for row in aligned:

                print(
                    f"{row['start_time']:>8.2f} - "
                    f"{row['end_time']:>8.2f} | "
                    f"{str(row['speaker']):<10} | "
                    f"{row['text']}"
                )

        else:

            print(
                "Aligned transcript not available."
            )

        # =================================================
        # SENTIMENT
        # =================================================

        # =================================================
        # SENTIMENT
        # =================================================

        section(
            "[6] SENTIMENT"
        )

        sentiment = conn.execute(
            """
            SELECT
                sentiment,
                sentiment_score,
                created_at
            FROM customer_analysis
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if sentiment:

            field(
                "Sentiment",
                sentiment["sentiment"]
            )

            field(
                "Sentiment Score",
                sentiment["sentiment_score"]
            )

            field(
                "Created At",
                sentiment["created_at"]
            )

        else:

            print(
                "Sentiment analysis not available."
            )

        # =================================================
        # EMOTION
        # =================================================

        section(
            "[7] EMOTION"
        )

        emotion = conn.execute(
            """
            SELECT *
            FROM customer_emotions
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if emotion:

            for key in emotion.keys():

                field(
                    key,
                    emotion[key]
                )

        else:

            print(
                "Emotion analysis not available."
            )

        # =================================================
        # ROOT CAUSE
        # =================================================

        section(
            "[8] ROOT CAUSE"
        )

        root_cause = conn.execute(
            """
            SELECT *
            FROM dissatisfaction_root_causes
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if root_cause:

            for key in root_cause.keys():

                field(
                    key,
                    root_cause[key]
                )

        else:

            print(
                "Root cause analysis not available."
            )

        # =================================================
        # CHURN RISK
        # =================================================

        section(
            "[9] CHURN RISK"
        )

        churn = conn.execute(
            """
            SELECT *
            FROM churn_risk_analysis
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (call_id,)
        ).fetchone()

        if not churn:

            print(
                "Churn risk analysis not available."
            )

        else:

            field(
                "Churn Risk Score",
                churn["churn_risk_score"]
            )

            field(
                "Churn Risk Level",
                churn["churn_risk_level"]
            )

            field(
                "Recovery Priority",
                churn["recovery_priority"]
            )

            field(
                "Customer Intent",
                churn["customer_intent"]
            )

            field(
                "Closure Intent",
                "YES"
                if churn["closure_intent"]
                else "NO"
            )

            field(
                "Fraud Intent",
                "YES"
                if churn["fraud_intent"]
                else "NO"
            )

            field(
                "Cross-Sell Suppression",
                "ACTIVE"
                if churn["cross_sell_suppression"]
                else "INACTIVE"
            )

            print_json_field(
                "Risk Factors",
                churn["risk_factors"]
            )

            print_json_field(
                "Score Breakdown",
                churn["score_breakdown"]
            )

        # =================================================
        # RETENTION RULES
        # =================================================

        section(
            "[10] RETENTION RULES"
        )

        if not churn:

            print(
                "No churn analysis available."
            )

        else:

            rules = parse_json(
                churn["triggered_rules"]
            )

            if not rules:

                print(
                    "No retention rules triggered."
                )

            elif isinstance(
                rules,
                list
            ):

                for rule in rules:

                    print(
                        f"{rule.get('rule_id')} | "
                        f"{rule.get('name')} | "
                        f"{rule.get('priority')}"
                    )

                    if rule.get("reason"):

                        print(
                            f"  Reason: "
                            f"{rule['reason']}"
                        )

                    recommendations = (
                        rule.get(
                            "recommendations"
                        )
                    )

                    if recommendations:

                        print(
                            "  Recommendations:"
                        )

                        for recommendation in (
                            recommendations
                        ):

                            print(
                                f"    • "
                                f"{recommendation}"
                            )

            else:

                print(
                    rules
                )

        # =================================================
        # RECOMMENDATION
        # =================================================

        section(
            "[11] RECOMMENDATION DECISION"
        )

        if not churn:

            print(
                "Recommendation decision "
                "not available."
            )

        else:

            recommendation = (
                parse_json(
                    churn[
                        "recommendation_decision"
                    ]
                )
            )

            if not recommendation:

                print(
                    "Recommendation decision "
                    "not available."
                )

            else:

                field(
                    "Outcome",
                    recommendation.get(
                        "outcome"
                    )
                )

                field(
                    "Priority",
                    recommendation.get(
                        "priority"
                    )
                )

                field(
                    "Primary Action",
                    recommendation.get(
                        "primary_action"
                    )
                )

                field(
                    "Response Time",
                    recommendation.get(
                        "response_time"
                    )
                )

                print()

                print(
                    "Reasons:"
                )

                reasons = recommendation.get(
                    "reason",
                    []
                )

                if isinstance(
                    reasons,
                    list
                ):

                    for reason in reasons:

                        print(
                            f"  • {reason}"
                        )

                else:

                    print(
                        f"  • {reasons}"
                    )

                print()

                field(
                    "Cross-Sell Suppression",
                    "ACTIVE"
                    if recommendation.get(
                        "cross_sell_suppression"
                    )
                    else "INACTIVE"
                )

        # =================================================
        # END
        # =================================================

        print()

        print("=" * 75)
        print("END OF CALL ANALYSIS")
        print("=" * 75)

    return 0


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python scripts/inspect_call.py <CALL_ID>"
        )

        sys.exit(1)

    sys.exit(
        inspect_call(
            sys.argv[1]
        )
    )
