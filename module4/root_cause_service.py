import json
import re

from agents.local_slm import LocalSLM


class RootCauseService:

    """
    Service responsible for identifying the primary
    dissatisfaction root cause from a customer conversation.

    The service uses the shared local Qwen3 SLM.

    Responsibilities:
        1. Build root-cause analysis prompt
        2. Send conversation to Qwen3
        3. Parse structured JSON response
        4. Validate the response
        5. Return normalized result

    Database operations are NOT performed here.
    Persistence is handled by RootCauseTool.
    """

    # =====================================================
    # ALLOWED ROOT-CAUSE CATEGORIES
    # =====================================================

    from config.settings import ROOT_CAUSE_CATEGORIES

    # ROOT_CAUSE_CATEGORIES = [

    #     "Fees / Charges",

    #     "Fraud / Unauthorized Transaction",

    #     "Mobile Banking",

    #     "Internet Banking",

    #     "Login / Authentication",

    #     "Loan Processing",

    #     "Account Opening",

    #     "Card Issue",

    #     "Service Delay",

    #     "Product Features",

    #     "Pricing / Interest Rate",

    #     "Poor Customer Service",

    #     "Other"
    # ]

    # =====================================================
    # ALLOWED SEVERITY VALUES
    # =====================================================

    SEVERITY_LEVELS = [

        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        model_path=None
    ):

        """
        Initialize the Root Cause Service.

        Parameters
        ----------
        model_path : optional
            Local Qwen3 model path.

            If None, LocalSLM uses the default:

                models/Qwen3
        """

        self.slm = LocalSLM(
            model_path=model_path
        )

    # =====================================================
    # PUBLIC METHOD
    # =====================================================

    def analyze(
        self,
        conversation_text
    ):
        """
        Analyze customer conversation and identify
        dissatisfaction root cause.

        Parameters
        ----------
        conversation_text : str
            Speaker-labelled customer conversation.

        Returns
        -------
        dict
            Structured root-cause analysis.
        """

        # -------------------------------------------------
        # Validate input
        # -------------------------------------------------

        if not conversation_text:

            return self._empty_result(
                reason=(
                    "No conversation text "
                    "was provided."
                )
            )

        conversation_text = str(
            conversation_text
        ).strip()

        if not conversation_text:

            return self._empty_result(
                reason=(
                    "Conversation text is empty."
                )
            )

        # -------------------------------------------------
        # Build prompt
        # -------------------------------------------------

        messages = (
            self._build_messages(
                conversation_text
            )
        )

        # -------------------------------------------------
        # Call Qwen3
        # -------------------------------------------------

        try:

            raw_response = (
                self.slm.generate(
                    messages,
                    max_new_tokens=400
                )
            )

        except Exception as e:

            raise RuntimeError(
                "Qwen3 root-cause analysis failed: "
                f"{str(e)}"
            ) from e

        # -------------------------------------------------
        # Parse response
        # -------------------------------------------------

        try:

            result = (
                self._parse_json_response(
                    raw_response
                )
            )

        except Exception as e:

            raise ValueError(
                "Unable to parse Qwen3 root-cause "
                "response: "
                f"{str(e)}\n\n"
                f"Raw response:\n{raw_response}"
            ) from e

        # -------------------------------------------------
        # Validate and normalize
        # -------------------------------------------------

        result = (
            self._validate_and_normalize(
                result
            )
        )

        return result

    # =====================================================
    # BUILD QWEN PROMPT
    # =====================================================

    def _build_messages(
        self,
        conversation_text
    ):
        """
        Build the system and user messages sent to Qwen3.
        """

        categories = "\n".join(

            f"- {category}"

            for category
            in self.ROOT_CAUSE_CATEGORIES
        )

        system_prompt = f"""
You are a banking Customer Experience
Root Cause Analysis AI.

Your task is to analyze a customer service
conversation and identify the PRIMARY reason
for customer dissatisfaction.

You must distinguish between:

1. The customer's emotion
2. The customer's sentiment
3. The actual business/problem causing
   dissatisfaction

For example:

Customer:
"I am extremely angry because you charged me
an annual card fee without informing me."

The emotion is anger.

The root cause is:
Fees / Charges.

Do NOT use the emotion as the root cause.

==================================================
ALLOWED ROOT-CAUSE CATEGORIES
==================================================

{categories}

You MUST select exactly ONE category.

==================================================
SEVERITY
==================================================

Use:

LOW
    Minor inconvenience or informational issue.

MEDIUM
    Meaningful service problem requiring
    normal intervention.

HIGH
    Significant dissatisfaction, repeated
    frustration, financial impact, service failure,
    or strong negative reaction.

CRITICAL
    Fraud, unauthorized transaction, account
    compromise, explicit relationship termination,
    or severe/high-value customer escalation.

==================================================
DISSATISFACTION
==================================================

Set:

dissatisfied = true

when the customer clearly expresses:
- complaint
- frustration
- anger
- disappointment
- dissatisfaction
- intent to escalate
- intent to leave
- financial/service grievance

Set:

dissatisfied = false

when the customer is primarily:
- asking a normal question
- seeking information
- requesting clarification
- having a neutral interaction
- expressing no meaningful dissatisfaction

==================================================
ROOT CAUSE
==================================================

Identify the PRIMARY underlying business problem.

Examples:

Unexpected bank fee
    -> Fees / Charges

Unauthorized card transaction
    -> Fraud / Unauthorized Transaction

Unable to login
    -> Login / Authentication

Mobile app not working
    -> Mobile Banking

Loan approval taking too long
    -> Loan Processing

Customer wants to close account
    -> Other

Poor interaction with bank employee
    -> Poor Customer Service

==================================================
EVIDENCE
==================================================

Provide a concise explanation of WHY this
root cause was selected.

Do not invent information.

Use only information supported by the
conversation.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Do NOT include:
- Markdown
- ```json
- explanations outside JSON
- additional fields

Required format:

{{
    "dissatisfied": true,
    "root_cause_category": "Fees / Charges",
    "root_cause": "Unexpected annual card fee",
    "severity": "HIGH",
    "confidence": 0.92,
    "evidence": "Customer states that an unexpected annual card fee was charged."
}}
"""

        user_prompt = f"""
Analyze the following banking customer
conversation.

==================================================
CONVERSATION
==================================================

{conversation_text}

==================================================
END CONVERSATION
==================================================

Return ONLY the required JSON.
"""

        return [

            {
                "role":
                    "system",

                "content":
                    system_prompt
            },

            {
                "role":
                    "user",

                "content":
                    user_prompt
            }
        ]

    # =====================================================
    # PARSE JSON RESPONSE
    # =====================================================

    def _parse_json_response(
        self,
        response
    ):
        """
        Extract JSON from Qwen3 response.

        Handles responses such as:

            {...}

        or:

            ```json
            {...}
            ```
        """

        if response is None:

            raise ValueError(
                "Empty model response."
            )

        response = str(
            response
        ).strip()

        if not response:

            raise ValueError(
                "Empty model response."
            )

        # -------------------------------------------------
        # Remove Markdown code fences
        # -------------------------------------------------

        response = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE
        )

        response = re.sub(
            r"```\s*",
            "",
            response
        )

        response = response.strip()

        # -------------------------------------------------
        # First attempt:
        # Parse entire response
        # -------------------------------------------------

        try:

            return json.loads(
                response
            )

        except json.JSONDecodeError:
            pass

        # -------------------------------------------------
        # Second attempt:
        # Extract JSON object
        # -------------------------------------------------

        start_index = (
            response.find("{")
        )

        end_index = (
            response.rfind("}")
        )

        if (
            start_index == -1
            or end_index == -1
            or end_index <= start_index
        ):

            raise ValueError(
                "No JSON object found in "
                "model response."
            )

        json_text = response[
            start_index:
            end_index + 1
        ]

        try:

            return json.loads(
                json_text
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                "Invalid JSON returned "
                "by Qwen3."
            ) from e

    # =====================================================
    # VALIDATE + NORMALIZE
    # =====================================================

    def _validate_and_normalize(
        self,
        result
    ):
        """
        Validate Qwen3 output and normalize
        fields for downstream database storage.
        """

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "Root cause result must "
                "be a JSON object."
            )

        # -------------------------------------------------
        # DISSATISFACTION
        # -------------------------------------------------

        dissatisfied = (
            result.get(
                "dissatisfied",
                False
            )
        )

        if isinstance(
            dissatisfied,
            str
        ):

            dissatisfied = (
                dissatisfied
                .strip()
                .lower()
                in [
                    "true",
                    "yes",
                    "1"
                ]
            )

        else:

            dissatisfied = bool(
                dissatisfied
            )

        # -------------------------------------------------
        # ROOT CAUSE CATEGORY
        # -------------------------------------------------

        category = (
            result.get(
                "root_cause_category"
            )
        )

        if category is None:

            category = "Other"

        category = str(
            category
        ).strip()

        # -------------------------------------------------
        # Match category robustly
        # -------------------------------------------------

        normalized_category = (
            self._match_category(
                category
            )
        )

        # -------------------------------------------------
        # ROOT CAUSE DESCRIPTION
        # -------------------------------------------------

        root_cause = (
            result.get(
                "root_cause"
            )
        )

        if root_cause is None:

            root_cause = ""

        root_cause = str(
            root_cause
        ).strip()

        # -------------------------------------------------
        # SEVERITY
        # -------------------------------------------------

        severity = (
            result.get(
                "severity"
            )
        )

        if severity is None:

            severity = "MEDIUM"

        severity = str(
            severity
        ).strip().upper()

        if severity not in (
            self.SEVERITY_LEVELS
        ):

            severity = "MEDIUM"

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        confidence = (
            result.get(
                "confidence",
                0.0
            )
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0

        # -------------------------------------------------
        # Clamp confidence
        # -------------------------------------------------

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        evidence = (
            result.get(
                "evidence"
            )
        )

        if evidence is None:

            evidence = ""

        evidence = str(
            evidence
        ).strip()

        # -------------------------------------------------
        # If not dissatisfied, normalize
        # root cause fields
        # -------------------------------------------------

        if not dissatisfied:

            normalized_category = (
                "Other"
            )

            severity = "LOW"

        # -------------------------------------------------
        # Final normalized result
        # -------------------------------------------------

        return {

            "dissatisfied":
                dissatisfied,

            "root_cause_category":
                normalized_category,

            "root_cause":
                root_cause,

            "severity":
                severity,

            "confidence":
                round(
                    confidence,
                    4
                ),

            "evidence":
                evidence
        }

    # =====================================================
    # CATEGORY MATCHING
    # =====================================================

    def _match_category(
        self,
        category
    ):
        """
        Match the model's category to one of the
        predefined categories.

        This protects the database from slightly
        different category names generated by Qwen3.
        """

        # -------------------------------------------------
        # Exact match
        # -------------------------------------------------

        for allowed_category in (
            self.ROOT_CAUSE_CATEGORIES
        ):

            if (
                category.lower()
                ==
                allowed_category.lower()
            ):

                return allowed_category

        # -------------------------------------------------
        # Keyword-based normalization
        # -------------------------------------------------

        category_lower = (
            category.lower()
        )

        keyword_mapping = {

            "fee":
                "Fees / Charges",

            "fees":
                "Fees / Charges",

            "charge":
                "Fees / Charges",

            "charges":
                "Fees / Charges",

            "fraud":
                "Fraud / Unauthorized Transaction",

            "unauthorized":
                "Fraud / Unauthorized Transaction",

            "unauthorised":
                "Fraud / Unauthorized Transaction",

            "hacked":
                "Fraud / Unauthorized Transaction",

            "mobile":
                "Mobile Banking",

            "app":
                "Mobile Banking",

            "internet":
                "Internet Banking",

            "online banking":
                "Internet Banking",

            "login":
                "Login / Authentication",

            "authentication":
                "Login / Authentication",

            "password":
                "Login / Authentication",

            "loan":
                "Loan Processing",

            "account opening":
                "Account Opening",

            "open account":
                "Account Opening",

            "card":
                "Card Issue",

            "delay":
                "Service Delay",

            "waiting":
                "Service Delay",

            "product":
                "Product Features",

            "feature":
                "Product Features",

            "interest":
                "Pricing / Interest Rate",

            "pricing":
                "Pricing / Interest Rate",

            "rate":
                "Pricing / Interest Rate",

            "customer service":
                "Poor Customer Service",

            "staff":
                "Poor Customer Service",

            "employee":
                "Poor Customer Service",

            "agent":
                "Poor Customer Service"
        }

        for keyword, mapped_category in (
            keyword_mapping.items()
        ):

            if keyword in category_lower:

                return mapped_category

        # -------------------------------------------------
        # Default
        # -------------------------------------------------

        return "Other"

    # =====================================================
    # EMPTY RESULT
    # =====================================================

    def _empty_result(
        self,
        reason=""
    ):
        """
        Return a safe result when no usable
        conversation is available.
        """

        return {

            "dissatisfied":
                False,

            "root_cause_category":
                "Other",

            "root_cause":
                "",

            "severity":
                "LOW",

            "confidence":
                0.0,

            "evidence":
                reason
        }