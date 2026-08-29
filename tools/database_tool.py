from database.database import (
    get_connection
)


class DatabaseTool:

    name = "get_call_analysis_state"

    description = """
    Check the current processing state of a call.

    Determines whether:
        - transcription exists
        - Whisper timestamped segments exist
        - diarization exists
        - speaker alignment exists
        - sentiment exists
        - emotion exists
        - root cause exists
    """

    def run(
        self,
        call_id: str
    ):

        with get_connection() as conn:

            # =================================================
            # CALL
            # =================================================

            call = conn.execute(
                """
                SELECT
                    call_id,
                    file_name,
                    file_path,
                    status
                FROM calls
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

            if not call:

                return {

                    "success":
                        False,

                    "call_exists":
                        False,

                    "error":
                        (
                            f"Call {call_id} "
                            f"does not exist."
                        )
                }

            # =================================================
            # TRANSCRIPT
            # =================================================

            transcript = conn.execute(
                """
                SELECT
                    transcript_id,
                    language,
                    duration,
                    full_text
                FROM transcripts
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            raw_segments = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM transcript_raw_segments
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

            raw_segment_count = (
                raw_segments["count"]
            )

            # =================================================
            # DIARIZATION
            # =================================================

            diarization = conn.execute(
                """
                SELECT
                    COUNT(*) AS segment_count,
                    COUNT(
                        DISTINCT speaker
                    ) AS speaker_count
                FROM diarization_segments
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

            diarization_segment_count = (
                diarization["segment_count"]
            )

            speaker_count = (
                diarization["speaker_count"]
            )

            # =================================================
            # ALIGNMENT
            # =================================================

            alignment = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM transcript_segments
                WHERE call_id = ?
                """,
                (call_id,)
            ).fetchone()

            alignment_segment_count = (
                alignment["count"]
            )

            # =================================================
            # SENTIMENT
            # =================================================

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

            # =================================================
            # EMOTION
            # =================================================

            emotion = conn.execute(
                """
                SELECT
                    primary_emotion,
                    emotion_score,
                    emotion_intensity,
                    confidence
                FROM customer_emotions
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()

            # =================================================
            # ROOT CAUSE
            # =================================================

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

            # =================================================
            # CHURN RISK
            # =================================================

            churn_risk = conn.execute(
                """
                SELECT
                    churn_risk_score,
                    churn_risk_level,
                    recovery_priority,
                    customer_intent,
                    closure_intent,
                    risk_factors,
                    score_breakdown,
                    triggered_rules,
                    recommendations,
                    cross_sell_suppression
                FROM churn_risk_analysis
                WHERE call_id = ?
                LIMIT 1
                """,
                (call_id,)
            ).fetchone()            

        # =====================================================
        # STATE
        # =====================================================

        return {

            "success":
                True,

            "call_exists":
                True,

            "call_id":
                call_id,

            "call_status":
                call["status"],

            "transcription_complete":
                (
                    transcript is not None
                    and raw_segment_count > 0
                ),

            "diarization_complete":
                (
                    diarization_segment_count > 0
                ),

            "alignment_complete":
                (
                    alignment_segment_count > 0
                ),

            "sentiment_complete":
                sentiment is not None,

            "emotion_complete":
                emotion is not None,

            "root_cause_complete":
                root_cause is not None,

            "churn_risk_complete":
                churn_risk is not None,                

            "speaker_count":
                speaker_count,

            "raw_segment_count":
                raw_segment_count,

            "diarization_segment_count":
                diarization_segment_count,

            "alignment_segment_count":
                alignment_segment_count,

            "sentiment":
                dict(sentiment)
                if sentiment
                else None,

            "emotion":
                dict(emotion)
                if emotion
                else None,

            "root_cause":
                dict(root_cause)
                if root_cause
                else None,

            "churn_risk":
                dict(churn_risk)
                if churn_risk
                else None                
        }