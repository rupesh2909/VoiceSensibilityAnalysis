import re


class ChurnRiskService:

    # =====================================================
    # SCORE WEIGHTS
    # =====================================================

    SENTIMENT_MAX = 20
    EMOTION_MAX = 20
    DISSATISFACTION_MAX = 20
    SEVERITY_MAX = 15
    CLOSURE_MAX = 25

    # =====================================================
    # RISK LEVELS
    # =====================================================

    def get_risk_level(
        self,
        score
    ):

        if score >= 75:
            return "CRITICAL"

        if score >= 50:
            return "HIGH"

        if score >= 25:
            return "MODERATE"

        return "LOW"

    # =====================================================
    # SENTIMENT SCORE
    # =====================================================

    def calculate_sentiment_points(
        self,
        sentiment,
        sentiment_score
    ):

        sentiment = str(
            sentiment or ""
        ).upper()

        try:
            score = float(
                sentiment_score
            )
        except (
            TypeError,
            ValueError
        ):
            score = 0.0

        # Negative sentiment
        if sentiment == "NEGATIVE":

            # Very negative
            if score <= -0.7:
                return 20

            # Moderately negative
            if score <= -0.4:
                return 15

            return 10

        # Neutral
        if sentiment == "NEUTRAL":
            return 3

        return 0

    # =====================================================
    # EMOTION SCORE
    # =====================================================

    def calculate_emotion_points(
        self,
        primary_emotion,
        anger_score,
        frustration_score,
        disappointment_score
    ):

        emotion = str(
            primary_emotion or ""
        ).upper()

        try:
            anger = float(
                anger_score or 0
            )
        except (
            TypeError,
            ValueError
        ):
            anger = 0

        try:
            frustration = float(
                frustration_score or 0
            )
        except (
            TypeError,
            ValueError
        ):
            frustration = 0

        try:
            disappointment = float(
                disappointment_score or 0
            )
        except (
            TypeError,
            ValueError
        ):
            disappointment = 0

        # Primary emotion receives strongest weight
        if emotion == "ANGER":

            return min(
                20,
                round(
                    10 + (
                        anger * 10
                    )
                )
            )

        if emotion == "FRUSTRATION":

            return min(
                20,
                round(
                    10 + (
                        frustration * 10
                    )
                )
            )

        if emotion == "DISAPPOINTMENT":

            return min(
                18,
                round(
                    8 + (
                        disappointment * 10
                    )
                )
            )

        if emotion == "CONFUSION":

            return 5

        return 0

    # =====================================================
    # DISSATISFACTION
    # =====================================================

    def calculate_dissatisfaction_points(
        self,
        dissatisfaction
    ):

        if str(
            dissatisfaction or ""
        ).upper() == "YES":

            return 20

        return 0

    # =====================================================
    # ROOT CAUSE SEVERITY
    # =====================================================

    def calculate_severity_points(
        self,
        severity
    ):

        severity = str(
            severity or ""
        ).upper()

        if severity == "HIGH":
            return 15

        if severity == "MEDIUM":
            return 10

        if severity == "LOW":
            return 5

        return 0

    # =====================================================
    # CLOSURE INTENT
    # =====================================================

    def detect_closure_intent(
        self,
        customer_text
    ):

        text = str(
            customer_text or ""
        ).lower()

        keywords = [
            "close account",
            "close my account",
            "cancel card",
            "cancel my card",
            "switch bank",
            "move my money",
            "move funds",
            "terminate relationship",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    # =====================================================
    # CLOSURE POINTS
    # =====================================================

    def calculate_closure_points(
        self,
        closure_intent
    ):

        if closure_intent:
            return 25

        return 0

    # =====================================================
    # MAIN SCORE
    # =====================================================

    def calculate_score(
        self,
        *,
        sentiment=None,
        sentiment_score=None,
        primary_emotion=None,
        anger_score=None,
        frustration_score=None,
        disappointment_score=None,
        dissatisfaction=None,
        severity=None,
        customer_text="",
    ):

        sentiment_points = (
            self.calculate_sentiment_points(
                sentiment,
                sentiment_score
            )
        )

        emotion_points = (
            self.calculate_emotion_points(
                primary_emotion,
                anger_score,
                frustration_score,
                disappointment_score
            )
        )

        dissatisfaction_points = (
            self.calculate_dissatisfaction_points(
                dissatisfaction
            )
        )

        severity_points = (
            self.calculate_severity_points(
                severity
            )
        )

        closure_intent = (
            self.detect_closure_intent(
                customer_text
            )
        )

        closure_points = (
            self.calculate_closure_points(
                closure_intent
            )
        )

        total = (
            sentiment_points
            + emotion_points
            + dissatisfaction_points
            + severity_points
            + closure_points
        )

        # Safety clamp
        total = max(
            0,
            min(
                100,
                total
            )
        )

        risk_level = (
            self.get_risk_level(
                total
            )
        )

        risk_factors = []

        if sentiment_points > 0:
            risk_factors.append(
                "Negative sentiment"
            )

        if emotion_points > 0:

            emotion_name = str(
                primary_emotion or ""
            ).upper()

            if emotion_name:
                risk_factors.append(
                    emotion_name.title()
                )

        if dissatisfaction_points > 0:
            risk_factors.append(
                "Customer dissatisfaction"
            )

        if severity_points > 0:
            risk_factors.append(
                f"{str(severity).title()} root cause severity"
            )

        if closure_intent:
            risk_factors.append(
                "Product closure intent"
            )

        return {

            "churn_risk_score":
                round(
                    total,
                    2
                ),

            "churn_risk_level":
                risk_level,

            "closure_intent":
                closure_intent,

            "risk_factors":
                risk_factors,

            "score_breakdown": {

                "sentiment":
                    sentiment_points,

                "emotion":
                    emotion_points,

                "dissatisfaction":
                    dissatisfaction_points,

                "severity":
                    severity_points,

                "closure_intent":
                    closure_points
            }
        }