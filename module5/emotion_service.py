import json
import re

from agents.local_slm import LocalSLM

from config.settings import (
    MAX_EMOTION_TEXT_LENGTH,
    EMOTION_CONFIDENCE_THRESHOLD
)


class EmotionService:

    # =====================================================
    # FEW-SHOT EXAMPLES
    # =====================================================

    EMOTION_EXAMPLES = """

EXAMPLE 1
Customer:
I am furious. This is completely unacceptable.
I have been charged this fee again.

Output:
{
    "primary_emotion": "ANGER",
    "emotion_score": 0.96,
    "anger_score": 0.96,
    "frustration_score": 0.88,
    "disappointment_score": 0.70,
    "confusion_score": 0.05,
    "fear_score": 0.02,
    "sadness_score": 0.10,
    "neutral_score": 0.01,
    "joy_score": 0.00,
    "surprise_score": 0.05,
    "emotion_intensity": 0.96,
    "confidence": 0.96,
    "evidence": "Customer explicitly expresses anger and describes the situation as unacceptable."
}


EXAMPLE 2
Customer:
I have contacted support several times and nobody has solved
the problem. I am really frustrated.

Output:
{
    "primary_emotion": "FRUSTRATION",
    "emotion_score": 0.94,
    "anger_score": 0.72,
    "frustration_score": 0.94,
    "disappointment_score": 0.78,
    "confusion_score": 0.10,
    "fear_score": 0.02,
    "sadness_score": 0.18,
    "neutral_score": 0.03,
    "joy_score": 0.00,
    "surprise_score": 0.02,
    "emotion_intensity": 0.94,
    "confidence": 0.94,
    "evidence": "Repeated unresolved support interactions are causing strong frustration."
}


EXAMPLE 3
Customer:
I expected much better from the bank. I am disappointed
that this happened.

Output:
{
    "primary_emotion": "DISAPPOINTMENT",
    "emotion_score": 0.91,
    "anger_score": 0.25,
    "frustration_score": 0.45,
    "disappointment_score": 0.91,
    "confusion_score": 0.05,
    "fear_score": 0.03,
    "sadness_score": 0.35,
    "neutral_score": 0.08,
    "joy_score": 0.00,
    "surprise_score": 0.12,
    "emotion_intensity": 0.91,
    "confidence": 0.91,
    "evidence": "Customer expresses disappointment with the bank's service."
}


EXAMPLE 4
Customer:
I don't understand why this charge appeared.
Can you explain what happened?

Output:
{
    "primary_emotion": "CONFUSION",
    "emotion_score": 0.88,
    "anger_score": 0.05,
    "frustration_score": 0.30,
    "disappointment_score": 0.15,
    "confusion_score": 0.88,
    "fear_score": 0.05,
    "sadness_score": 0.05,
    "neutral_score": 0.20,
    "joy_score": 0.00,
    "surprise_score": 0.25,
    "emotion_intensity": 0.30,
    "confidence": 0.88,
    "evidence": "Customer is primarily seeking clarification about an unexpected charge."
}


EXAMPLE 5
Customer:
Thank you for resolving this so quickly.
I really appreciate your help.

Output:
{
    "primary_emotion": "JOY",
    "emotion_score": 0.93,
    "anger_score": 0.00,
    "frustration_score": 0.01,
    "disappointment_score": 0.00,
    "confusion_score": 0.01,
    "fear_score": 0.00,
    "sadness_score": 0.00,
    "neutral_score": 0.10,
    "joy_score": 0.93,
    "surprise_score": 0.05,
    "emotion_intensity": 0.93,
    "confidence": 0.93,
    "evidence": "Customer expresses appreciation and satisfaction."
}


EXAMPLE 6
Customer:
Okay. I understand. That is all I needed to know.

Output:
{
    "primary_emotion": "NEUTRAL",
    "emotion_score": 0.75,
    "anger_score": 0.02,
    "frustration_score": 0.03,
    "disappointment_score": 0.02,
    "confusion_score": 0.05,
    "fear_score": 0.01,
    "sadness_score": 0.01,
    "neutral_score": 0.75,
    "joy_score": 0.10,
    "surprise_score": 0.04,
    "emotion_intensity": 0.05,
    "confidence": 0.75,
    "evidence": "Customer expresses a calm and neutral response."
}

"""

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        print(
            "Initializing Qwen3 emotion service..."
        )

        self.slm = LocalSLM()

        print(
            "Qwen3 emotion service ready."
        )

    # =====================================================
    # ANALYZE
    # =====================================================

    def analyze(
        self,
        text
    ):

        if not text or not text.strip():

            raise ValueError(
                "Text cannot be empty."
            )

        text = text[
            :MAX_EMOTION_TEXT_LENGTH
        ]

        messages = self._build_messages(
            text
        )

        try:

            raw_response = (
                self.slm.generate(
                    messages,
                    max_new_tokens=400
                )
            )

        except Exception as e:

            raise RuntimeError(
                "Qwen3 emotion analysis failed: "
                f"{str(e)}"
            ) from e

        try:

            result = (
                self._parse_json_response(
                    raw_response
                )
            )

        except Exception as e:

            raise ValueError(
                "Unable to parse Qwen3 emotion "
                "response: "
                f"{str(e)}\n\n"
                f"Raw response:\n{raw_response}"
            ) from e

        return self._validate_and_normalize(
            result
        )

    # =====================================================
    # BUILD PROMPT
    # =====================================================

    def _build_messages(
        self,
        conversation_text
    ):

        system_prompt = """
You are a customer emotion analysis system
for a banking customer-call analytics platform.

Analyze ONLY the customer's emotional state.

Do not analyze the agent.

Choose the single most prominent primary emotion.

Allowed primary emotions:

ANGER
FRUSTRATION
DISAPPOINTMENT
CONFUSION
FEAR
SADNESS
NEUTRAL
JOY
SURPRISE

Return ONLY valid JSON.

All scores must be numbers between 0.0 and 1.0.

emotion_intensity represents the strongest
emotion expressed by the customer.

confidence represents confidence in the
primary emotion classification.

Evidence must be a short factual explanation
based only on the customer's words.
"""

        user_prompt = f"""
Use these few-shot examples as guidance.

{self.EMOTION_EXAMPLES}

Now analyze this customer conversation:

Customer:
{conversation_text}

Return ONLY this JSON structure:

{{
    "primary_emotion": "ANGER | FRUSTRATION | DISAPPOINTMENT | CONFUSION | FEAR | SADNESS | NEUTRAL | JOY | SURPRISE",
    "emotion_score": 0.0,
    "anger_score": 0.0,
    "frustration_score": 0.0,
    "disappointment_score": 0.0,
    "confusion_score": 0.0,
    "fear_score": 0.0,
    "sadness_score": 0.0,
    "neutral_score": 0.0,
    "joy_score": 0.0,
    "surprise_score": 0.0,
    "emotion_intensity": 0.0,
    "confidence": 0.0,
    "evidence": ""
}}
"""

        return [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

    # =====================================================
    # PARSE JSON
    # =====================================================

    def _parse_json_response(
        self,
        response
    ):

        if isinstance(
            response,
            dict
        ):

            return response

        response = str(
            response
        ).strip()

        response = re.sub(
            r"```(?:json)?",
            "",
            response,
            flags=re.IGNORECASE
        ).replace(
            "```",
            ""
        ).strip()

        try:

            result = json.loads(
                response
            )

            if isinstance(
                result,
                dict
            ):

                return result

        except json.JSONDecodeError:
            pass

        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL
        )

        if not match:

            raise ValueError(
                "No JSON object found."
            )

        result = json.loads(
            match.group(0)
        )

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "JSON response is not an object."
            )

        return result

    # =====================================================
    # VALIDATE / NORMALIZE
    # =====================================================

    def _validate_and_normalize(
        self,
        result
    ):

        allowed_emotions = {
            "ANGER",
            "FRUSTRATION",
            "DISAPPOINTMENT",
            "CONFUSION",
            "FEAR",
            "SADNESS",
            "NEUTRAL",
            "JOY",
            "SURPRISE"
        }

        primary_emotion = str(
            result.get(
                "primary_emotion",
                "UNCERTAIN"
            )
        ).upper().strip()

        if primary_emotion not in allowed_emotions:

            primary_emotion = "UNCERTAIN"

        def score(
            key
        ):

            try:

                value = float(
                    result.get(
                        key,
                        0.0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                value = 0.0

            return max(
                0.0,
                min(
                    1.0,
                    value
                )
            )

        emotion_score = score(
            "emotion_score"
        )

        anger_score = score(
            "anger_score"
        )

        frustration_score = score(
            "frustration_score"
        )

        disappointment_score = score(
            "disappointment_score"
        )

        confusion_score = score(
            "confusion_score"
        )

        fear_score = score(
            "fear_score"
        )

        sadness_score = score(
            "sadness_score"
        )

        neutral_score = score(
            "neutral_score"
        )

        joy_score = score(
            "joy_score"
        )

        surprise_score = score(
            "surprise_score"
        )

        emotion_intensity = score(
            "emotion_intensity"
        )

        confidence = score(
            "confidence"
        )

        if (
            confidence
            < EMOTION_CONFIDENCE_THRESHOLD
        ):

            primary_emotion = "UNCERTAIN"

        return {

            "primary_emotion":
                primary_emotion,

            "emotion_score":
                emotion_score,

            "anger_score":
                anger_score,

            "frustration_score":
                frustration_score,

            "disappointment_score":
                disappointment_score,

            "confusion_score":
                confusion_score,

            "fear_score":
                fear_score,

            "sadness_score":
                sadness_score,

            "neutral_score":
                neutral_score,

            "joy_score":
                joy_score,

            "surprise_score":
                surprise_score,

            "emotion_intensity":
                emotion_intensity,

            "confidence":
                confidence,

            "evidence":
                str(
                    result.get(
                        "evidence",
                        ""
                    )
                ).strip()
        }
