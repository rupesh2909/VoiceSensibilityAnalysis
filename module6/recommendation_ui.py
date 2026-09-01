"""
Module 6 — Recommendation Engine UI

Presentation layer for the deterministic recommendation engine.
"""

import streamlit as st


# =========================================================
# CARD HELPERS
# =========================================================

def _render_metric_card(
    title,
    value,
    icon="",
):
    """
    Render a compact recommendation metric card.
    """

    with st.container(border=True):

        st.markdown(
            f"**{icon} {title}**"
        )

        st.markdown(
            f"### {value}"
        )


def _render_list_card(
    title,
    items,
    icon="",
):
    """
    Render a recommendation content card.
    """

    with st.container(border=True):

        st.markdown(
            f"**{icon} {title}**"
        )

        if not items:

            st.markdown(
                "None"
            )

            return

        for item in items:

            st.markdown(
                f"- {item}"
            )


# =========================================================
# MAIN RENDERER
# =========================================================

def render_recommendation(
    recommendation_decision
):
    """
    Render the deterministic recommendation decision.

    This function only presents the decision.
    It does not calculate business rules.
    """

    if not recommendation_decision:
        recommendation_decision = {
            "outcome": "NO_IMMEDIATE_RECOVERY_REQUIRED",
            "priority": "LOW",
            "primary_action": "Continue normal servicing",
            "response_time": None,
            "reason": "No retention or recovery rule was triggered.",
            "triggered_rules": [],
            "recommendations": [
                "Continue normal servicing"
            ],
            "cross_sell_suppression": False,
        }

    outcome = (
        recommendation_decision.get(
            "outcome"
        )
    )

    priority = (
        recommendation_decision.get(
            "priority",
            "LOW"
        )
    )

    primary_action = (
        recommendation_decision.get(
            "primary_action",
            "Continue normal servicing"
        )
    )

    response_time = (
        recommendation_decision.get(
            "response_time"
        )
    )

    reasons = (
        recommendation_decision.get(
            "reason",
            []
        )
    )

    recommendations = (
        recommendation_decision.get(
            "recommendations",
            []
        )
    )

    cross_sell_suppression = (
        recommendation_decision.get(
            "cross_sell_suppression",
            False
        )
    )

    # -----------------------------------------------------
    # Normalize
    # -----------------------------------------------------

    if isinstance(
        reasons,
        str
    ):
        reasons = [reasons]

    # -----------------------------------------------------
    # Heading
    # -----------------------------------------------------

    st.markdown(
        "### 🎯 Manager Recommendation"
    )

    # =====================================================
    # NO IMMEDIATE RECOVERY
    # =====================================================

    if outcome == (
        "NO_IMMEDIATE_RECOVERY_REQUIRED"
    ):

        col1, col2 = st.columns(2)

        with col1:

            _render_metric_card(
                "PRIORITY",
                "LOW",
                "🟢"
            )

        with col2:

            _render_metric_card(
                "OUTCOME",
                "No Immediate Recovery Required",
                "✓"
            )

        st.markdown("")

        col1, col2 = st.columns(2)

        with col1:

            _render_list_card(
                "WHY?",
                reasons or [
                    "No immediate recovery rule was triggered."
                ],
                "ℹ️"
            )

        with col2:

            _render_list_card(
                "RECOMMENDED ACTION",
                [
                    "Continue normal servicing"
                ],
                "📋"
            )

        return

    # =====================================================
    # RECOVERY REQUIRED
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        if priority == "CRITICAL":
            priority_icon = "🔴"

        elif priority == "HIGH":
            priority_icon = "🟠"

        else:
            priority_icon = "🟡"

        _render_metric_card(
            "PRIORITY",
            priority,
            priority_icon
        )

    with col2:

        _render_metric_card(
            "PRIMARY ACTION",
            primary_action,
            "🎯"
        )

    with col3:

        _render_metric_card(
            "RESPONSE TIME",
            response_time or "Manager review",
            "⏱️"
        )

    st.markdown("")

    # =====================================================
    # WHY + ACTIONS
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:

        _render_list_card(
            "WHY THIS CUSTOMER IS AT RISK?",
            reasons,
            "⚠️"
        )

    with col2:

        _render_list_card(
            "RECOMMENDED ACTIONS",
            recommendations,
            "📋"
        )

    # =====================================================
    # CROSS-SELL SUPPRESSION
    # =====================================================

    if cross_sell_suppression:

        st.markdown("")

        with st.container(border=True):

            st.markdown(
                "### 🚫 Cross-Sell Suppression — ACTIVE"
            )

            st.markdown(
                "Suspend promotional activity and focus only "
                "on customer recovery actions."
            )