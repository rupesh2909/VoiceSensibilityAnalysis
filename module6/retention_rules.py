"""
Module 6 — Rule-Based Retention Recommendation Engine

Evaluates the MVP retention rules against the outputs
of Modules 3, 4 and 5.

The rule engine is deterministic and explainable.
It does not use Qwen3 to invent recommendations.
"""

import re

from config.settings import (
    RETENTION_SENTIMENT_THRESHOLD,
    RETENTION_ANGER_THRESHOLD,
    HIGH_VALUE_CUSTOMER_VALUES,
)

# =========================================================
# PRIORITY RANKING
# =========================================================

PRIORITY_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


# =========================================================
# KEYWORD GROUPS
# =========================================================

FRAUD_KEYWORDS = [
    "fraud",
    "unauthorized transaction",
    "card misuse",
    "account hacked",
]

CLOSURE_KEYWORDS = [
    "close account",
    "close my account",
    "cancel card",
    "cancel my card",
    "switch bank",
    "move my money",
    "move funds",
    "terminate relationship",
]

DIGITAL_BANKING_KEYWORDS = [
    "mobile banking",
    "internet banking",
    "online banking",
    "login",
    "log in",
    "logged in",
    "password",
    "authentication",
]

SERVICE_DELAY_CATEGORIES = {
    "LOAN PROCESSING",
    "DISPUTE RESOLUTION",
    "ACCOUNT OPENING",
}

FEE_CATEGORIES = {
    "FEES / CHARGES",
    "PRICING / INTEREST RATE",
}


# =========================================================
# TEXT MATCHING
# =========================================================

def contains_keyword(text, keywords):
    """
    Case-insensitive keyword/phrase matching.
    """

    text = str(text or "").lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# =========================================================
# RULE 1
# =========================================================

def rule_high_anger_high_value(
    sentiment,
    sentiment_score,
    anger_score=None,
    customer_value=None,
    call_duration=None
):
    """
    Rule 1:
    High Anger + High Customer Value

    Required:
        Sentiment = NEGATIVE
        Sentiment confidence >= 0.70
        Anger Score >= 0.70
        Customer Value = Platinum / High AUM
    """

    if customer_value is None:
        return None

    try:
        score = float(
            sentiment_score
        )

        anger = float(
            anger_score
        )

        duration = float(
            call_duration or 0
        )

    except (
        TypeError,
        ValueError
    ):
        return None

    high_value = str(
        customer_value
    ).upper() in HIGH_VALUE_CUSTOMER_VALUES

    negative = (
        str(
            sentiment or ""
        ).upper()
        == "NEGATIVE"
    )

    if (
        negative
        and score >= RETENTION_SENTIMENT_THRESHOLD
        and anger >= RETENTION_ANGER_THRESHOLD
        and high_value
    ):

        return {
            "rule_id": "RULE_1",

            "name":
                "High Anger + High Customer Value",

            "priority":
                "CRITICAL",

            "reason": (
                "Customer sentiment is strongly negative "
                f"(confidence {score:.2f}), "
                f"anger score is {anger:.2f}, "
                "and customer has high value."
            ),

            "recommendations": [
                "Immediate Relationship Manager callback within 2 hours",
                "Service Recovery Case creation",
                "Escalation to Retention Team",
            ],
        }

    return None


# =========================================================
# RULE 2
# =========================================================

def rule_fraud_complaint(customer_text):
    """
    Rule 2:
    Fraud or Unauthorized Transaction Complaint
    """

    if not contains_keyword(
        customer_text,
        FRAUD_KEYWORDS
    ):
        return None

    return {
        "rule_id": "RULE_2",
        "name": "Fraud or Unauthorized Transaction Complaint",
        "priority": "CRITICAL",
        "reason": (
            "Fraud or unauthorized transaction "
            "language detected in customer conversation."
        ),
        "recommendations": [
            "Trigger Fraud Investigation Workflow",
            "Send proactive status updates",
            "Assign dedicated case owner",
        ],
    }


# =========================================================
# RULE 3
# =========================================================

def rule_digital_banking_frustration(
    sentiment,
    root_cause_category,
    customer_text,
):
    """
    Rule 3:
    Digital Banking Frustration
    """

    negative = str(
        sentiment or ""
    ).upper() in {
        "NEGATIVE",
        "DISSATISFIED",
    }

    category = str(
        root_cause_category or ""
    ).upper()

    digital_root_cause = (
        "MOBILE BANKING" in category
        or "INTERNET BANKING" in category
        or "LOGIN" in category
        or "AUTHENTICATION" in category
    )

    if not (
        negative
        and digital_root_cause
    ):
        return None

    return {
        "rule_id": "RULE_3",
        "name": "Digital Banking Frustration",
        "priority": "HIGH",
        "reason": (
            "Negative sentiment combined with "
            "digital banking or login-related issues."
        ),
        "recommendations": [
            "Share self-service guides",
            "Priority technical support callback",
            "Offer assisted onboarding",
        ],
    }


# =========================================================
# RULE 4
# =========================================================

def rule_repeated_complaint(
    customer_call_count_30d=None,
    similar_issue=False,
):
    """
    Rule 4:
    Repeated Complaint Customer
    """

    if customer_call_count_30d is None:
        return None

    try:
        call_count = int(
            customer_call_count_30d
        )
    except (TypeError, ValueError):
        return None

    if (
        call_count > 3
        and similar_issue
    ):
        return {
            "rule_id": "RULE_4",
            "name": "Repeated Complaint Customer",
            "priority": "HIGH",
            "reason": (
                "Customer has called more than three "
                "times in 30 days about a similar issue."
            ),
            "recommendations": [
                "Escalate to Specialized Support Team",
                "Open Customer Experience Review Case",
            ],
        }

    return None


# =========================================================
# RULE 5
# =========================================================

def rule_product_closure_intent(closure_intent):
    """
    Rule 5:
    Product Closure Intent
    """

    if closure_intent != "YES":
        return None

    return {
        "rule_id": "RULE_5",
        "name": "Product Closure Intent",
        "priority": "CRITICAL",
        "reason": (
            "Customer expressed intent to close, "
            "cancel, switch or terminate the relationship."
        ),
        "recommendations": [
            "Retention Team Engagement",
            "Personalized Offer Generation",
            "Manager Callback",
        ],
    }


# =========================================================
# RULE 6
# =========================================================

def rule_pricing_fee_complaint(
    root_cause_category,
):
    """
    Rule 6:
    Pricing / Fee Complaint
    """

    category = str(
        root_cause_category or ""
    ).upper()

    if category not in FEE_CATEGORIES:
        return None

    return {
        "rule_id": "RULE_6",
        "name": "Pricing / Fee Complaint",
        "priority": "HIGH",
        "reason": (
            "Root cause is related to fees, "
            "charges or pricing."
        ),
        "recommendations": [
            "Fee Reversal Eligibility Check",
            "Relationship Pricing Review",
            "Product Upgrade Recommendation",
        ],
    }


# =========================================================
# RULE 7
# =========================================================

def rule_service_delay(
    root_cause_category,
    frustration_score,
    frustration_threshold=0.60,
):
    """
    Rule 7:
    Service Delay Complaint
    """

    category = str(
        root_cause_category or ""
    ).upper()

    try:
        frustration = float(
            frustration_score or 0
        )
    except (TypeError, ValueError):
        frustration = 0

    if (
        category in SERVICE_DELAY_CATEGORIES
        and frustration > frustration_threshold
    ):
        return {
            "rule_id": "RULE_7",
            "name": "Service Delay Complaint",
            "priority": "MEDIUM",
            "reason": (
                "Service-delay root cause detected "
                "with elevated frustration."
            ),
            "recommendations": [
                "Case Status Explanation",
                "Priority Service Ticket",
                "Proactive Progress Tracking",
            ],
        }

    return None


# =========================================================
# RULE 8
# =========================================================

def rule_customer_confusion(
    emotion,
    sentiment,
):
    """
    Rule 8:
    Customer Confusion (Not Angry)
    """

    is_confused = (
        str(emotion or "").upper()
        == "CONFUSION"
    )

    is_neutral = (
        str(sentiment or "").upper()
        == "NEUTRAL"
    )

    if not (
        is_confused
        and is_neutral
    ):
        return None

    return {
        "rule_id": "RULE_8",
        "name": "Customer Confusion (Not Angry)",
        "priority": "MEDIUM",
        "reason": (
            "Customer appears confused while "
            "sentiment remains neutral."
        ),
        "recommendations": [
            "Educational Content",
            "Product Walkthrough",
            "Advisor Consultation",
        ],
    }


# =========================================================
# RULE 9
# =========================================================

def rule_vip_dissatisfaction(
    customer_segment=None,
    sentiment=None,
):
    """
    Rule 9:
    VIP Customer Dissatisfaction
    """

    if customer_segment is None:
        return None

    vip = str(
        customer_segment
    ).upper() in {
        "PREMIUM",
        "CORPORATE",
    }

    negative = str(
        sentiment or ""
    ).upper() in {
        "NEGATIVE",
        "DISSATISFIED",
    }

    if not (
        vip
        and negative
    ):
        return None

    return {
        "rule_id": "RULE_9",
        "name": "VIP Customer Dissatisfaction",
        "priority": "CRITICAL",
        "reason": (
            "VIP customer segment combined "
            "with negative sentiment."
        ),
        "recommendations": [
            "Branch Manager Notification",
            "Personalized Outreach",
            "Concierge Service Follow-Up",
        ],
    }


# =========================================================
# RULE 10
# =========================================================

def rule_cross_sell_suppression(
    churn_risk_score,
    sentiment,
):
    """
    Rule 10:
    Cross-Sell Suppression
    """

    try:
        churn_score = float(
            churn_risk_score
        )
    except (TypeError, ValueError):
        return None

    negative = str(
        sentiment or ""
    ).upper() in {
        "NEGATIVE",
        "DISSATISFIED",
    }

    if (
        churn_score > 75
        and negative
    ):
        return {
            "rule_id": "RULE_10",
            "name": "Cross-Sell Suppression",
            "priority": "BUSINESS_RULE",
            "reason": (
                "Churn risk exceeds 75 while "
                "customer sentiment is negative."
            ),
            "recommendations": [
                "Suspend Marketing Campaigns",
                "Do NOT send promotional offers",
                "Focus only on Recovery Actions",
            ],
        }

    return None


# =========================================================
# RULE ENGINE
# =========================================================

def evaluate_rules(
    *,
    customer_text="",
    sentiment=None,
    sentiment_score=None,
    emotion=None,
    anger_score=None,
    frustration_score=None,
    root_cause_category=None,
    churn_risk_score=None,
    customer_value=None,
    call_duration=None,
    customer_call_count_30d=None,
    similar_issue=False,
    customer_segment=None,
    closure_intent=None,
):
    """
    Evaluate all MVP retention rules.

    Returns only rules whose conditions are satisfied.
    """

    rules = []

    result = rule_high_anger_high_value(
        sentiment,
        sentiment_score,
        anger_score,
        customer_value,
        call_duration,
    )

    if result:
        rules.append(result)

    result = rule_fraud_complaint(
        customer_text
    )

    if result:
        rules.append(result)

    result = rule_digital_banking_frustration(
        sentiment,
        root_cause_category,
        customer_text,
    )

    if result:
        rules.append(result)

    result = rule_repeated_complaint(
        customer_call_count_30d,
        similar_issue,
    )

    if result:
        rules.append(result)

    result = rule_product_closure_intent(
        closure_intent
    )

    if result:
        rules.append(result)

    result = rule_pricing_fee_complaint(
        root_cause_category
    )

    if result:
        rules.append(result)

    result = rule_service_delay(
        root_cause_category,
        frustration_score,
    )

    if result:
        rules.append(result)

    result = rule_customer_confusion(
        emotion,
        sentiment,
    )

    if result:
        rules.append(result)

    result = rule_vip_dissatisfaction(
        customer_segment,
        sentiment,
    )

    if result:
        rules.append(result)

    result = rule_cross_sell_suppression(
        churn_risk_score,
        sentiment,
    )

    if result:
        rules.append(result)

    return rules


# =========================================================
# AGGREGATE RECOMMENDATIONS
# =========================================================

def aggregate_recommendations(
    triggered_rules
):
    """
    Combine recommendations from all triggered rules
    while preserving order and removing duplicates.
    """

    recommendations = []

    for rule in triggered_rules:

        for recommendation in rule.get(
            "recommendations",
            []
        ):

            if recommendation not in recommendations:

                recommendations.append(
                    recommendation
                )

    return recommendations


# =========================================================
# HIGHEST PRIORITY
# =========================================================

def get_highest_priority(
    triggered_rules
):
    """
    Return the highest recovery priority.
    """

    if not triggered_rules:
        return "LOW"

    priorities = [
        rule.get(
            "priority",
            "LOW"
        )

        for rule in triggered_rules

        if rule.get(
            "priority"
        ) != "BUSINESS_RULE"
    ]

    if not priorities:
        return "LOW"

    return max(
        priorities,
        key=lambda priority:
            PRIORITY_RANK.get(
                priority,
                0
            )
    )

# =========================================================
# BUILD RECOMMENDATION DECISION
# =========================================================

def build_recommendation_decision(
    triggered_rules,
    churn_risk_score=None,
    sentiment=None,
):
    """
    Convert triggered retention rules into a
    manager-friendly recommendation decision.

    This function does not make new business decisions.
    It only aggregates the deterministic rule results.
    """

    triggered_rules = (
        triggered_rules
        or []
    )

    # -----------------------------------------------------
    # No recovery rule triggered
    # -----------------------------------------------------

    if not triggered_rules:

        return {
            "outcome":
                "NO_IMMEDIATE_RECOVERY_REQUIRED",

            "priority":
                "LOW",

            "primary_action":
                "Continue normal servicing",

            "response_time":
                None,

            "reason":
                "No immediate recovery rule was triggered.",

            "triggered_rules":
                [],

            "recommendations": [
                "Continue normal servicing"
            ],

            "cross_sell_suppression":
                False
        }

    # -----------------------------------------------------
    # Overall priority
    # -----------------------------------------------------

    priority = (
        get_highest_priority(
            triggered_rules
        )
    )

    # -----------------------------------------------------
    # Aggregate recommendations
    # -----------------------------------------------------

    recommendations = (
        aggregate_recommendations(
            triggered_rules
        )
    )

    # -----------------------------------------------------
    # Cross-sell suppression
    # -----------------------------------------------------

    cross_sell_suppression = any(
        rule.get("rule_id")
        == "RULE_10"

        for rule in triggered_rules
    )

    # -----------------------------------------------------
    # Primary action / response time
    # -----------------------------------------------------

    primary_action = (
        recommendations[0]
        if recommendations
        else "Manager review required"
    )

    response_time = None

    rule_ids = {
        rule.get("rule_id")
        for rule in triggered_rules
    }

    # Rule 2 — Fraud / Unauthorized Transaction
    if "RULE_2" in rule_ids:

        primary_action = (
            "Trigger Fraud Investigation Workflow"
        )

        response_time = (
            "Immediate"
        )

    # Rule 5 — Product Closure Intent
    elif "RULE_5" in rule_ids:

        primary_action = (
            "Manager Callback"
        )

        response_time = (
            "Immediate"
        )

    # Rule 1 — High Anger + High Customer Value
    elif "RULE_1" in rule_ids:

        primary_action = (
            "Immediate Relationship Manager callback"
        )

        response_time = (
            "Within 2 hours"
        )

    # Rule 9 — VIP Customer Dissatisfaction
    elif "RULE_9" in rule_ids:

        primary_action = (
            "Branch Manager Notification"
        )

        response_time = (
            "Within 2 hours"
        )

    # Any High-priority recovery
    elif priority == "HIGH":

        response_time = (
            "Within 24 hours"
        )

    # Any Medium-priority recovery
    elif priority == "MEDIUM":

        response_time = (
            "Within 48 hours"
        )

    # -----------------------------------------------------
    # Explain why the recommendation was generated
    # -----------------------------------------------------

    reasons = []

    for rule in triggered_rules:

        reason = rule.get(
            "reason"
        )

        if reason:
            reasons.append(
                reason
            )

    return {
        "outcome":
            "RECOVERY_REQUIRED",

        "priority":
            priority,

        "primary_action":
            primary_action,

        "response_time":
            response_time,

        "reason":
            reasons,

        "triggered_rules":
            triggered_rules,

        "recommendations":
            recommendations,

        "cross_sell_suppression":
            cross_sell_suppression
    }    