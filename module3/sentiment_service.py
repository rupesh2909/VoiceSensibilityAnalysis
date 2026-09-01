import json
import re

from agents.local_slm import LocalSLM

from config.settings import (
    MAX_SENTIMENT_TEXT_LENGTH
)


class SentimentService:

    # =====================================================
    # FEW-SHOT EXAMPLES
    # =====================================================

    SENTIMENT_EXAMPLES = """

EXAMPLE 1
Customer:
I am extremely happy with the service. Thank you for resolving
my issue so quickly.

Output:
{
    "sentiment": "POSITIVE",
    "score": 0.95
}


EXAMPLE 2
Customer:
I have called several times and nobody has fixed this.
I am extremely frustrated with the service.

Output:
{
    "sentiment": "NEGATIVE",
    "score": 0.96
}


EXAMPLE 3
Customer:
Okay, I understand. Thank you for checking.

Output:
{
    "sentiment": "NEUTRAL",
    "score": 0.72
}


EXAMPLE 4
Customer:
This is absolutely unacceptable. If this is not fixed today,
I am going to close my account.

Output:
{
    "sentiment": "NEGATIVE",
    "score": 0.98
}

"""

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        print(
            "Initializing Qwen3 sentiment service..."
        )

        self.slm = LocalSLM()

        print(
            "Qwen3 sentiment service ready."
        )

    # =====================================================
    # ANALYZE
    # =====================================================

    def analyze(
        self,
        text
    ):

        if not text or not text.strip():

            return {
                "sentiment": "UNKNOWN",
                "score": 0.0
            }

        text = text[
            :MAX_SENTIMENT_TEXT_LENGTH
        ]

        messages = self._build_messages(
            text
        )

        try:

            raw_response = (
                self.slm.generate(
                    messages,
                    max_new_tokens=150
                )
            )

        except Exception as e:

            raise RuntimeError(
                "Qwen3 sentiment analysis failed: "
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
                "Unable to parse Qwen3 sentiment "
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
You are a customer sentiment analysis system
for a banking customer-call analytics platform.

Analyze ONLY the customer's sentiment.

Do not analyze the agent's sentiment.

Allowed sentiment labels:

POSITIVE
NEGATIVE
NEUTRAL

Return ONLY valid JSON.

The score must be a number between 0.0 and 1.0
representing your confidence in the classification.

Do not include markdown.
Do not include explanations outside the JSON.
"""

        user_prompt = f"""
Use the following few-shot examples as guidance.

{self.SENTIMENT_EXAMPLES}

Now analyze this customer conversation:

Customer:
{conversation_text}

Return ONLY:

{{
    "sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
    "score": 0.0
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

        # Remove markdown fences if Qwen
        # happens to return them.

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

        # Try extracting the first JSON object.

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

        sentiment = str(
            result.get(
                "sentiment",
                "UNKNOWN"
            )
        ).upper().strip()

        if sentiment not in {
            "POSITIVE",
            "NEGATIVE",
            "NEUTRAL"
        }:

            sentiment = "UNKNOWN"

        try:

            score = float(
                result.get(
                    "score",
                    0.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0.0

        score = max(
            0.0,
            min(
                1.0,
                score
            )
        )

        return {
            "sentiment": sentiment,
            "score": score
        }
