import json

import streamlit as st

from database.database import (
    get_connection
)

from tools.churn_risk_tool import (
    ChurnRiskTool
)


# =========================================================
# GET AVAILABLE CALLS
# =========================================================

def get_available_calls():

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT
                call_id,
                file_name,
                status,
                created_at

            FROM calls

            ORDER BY created_at DESC
            """
        ).fetchall()


# =========================================================
# DISPLAY SCORE
# =========================================================

def display_churn_score(
    result
):

    st.markdown(
        "## 🎯 Customer Churn Risk"
    )

    score = result.get(
        "churn_risk_score",
        0
    )

    level = result.get(
        "churn_risk_level",
        "N/A"
    )

    priority = result.get(
        "recovery_priority",
        "N/A"
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Churn Risk Score",
            f"{score:.0f} / 100"
        )

    with col2:

        st.metric(
            "Risk Level",
            level
        )

    with col3:

        st.metric(
            "Recovery Priority",
            priority
        )

    # -----------------------------------------------------
    # Risk indicator
    # -----------------------------------------------------

    if level == "CRITICAL":

        st.error(
            "🔴 CRITICAL CHURN RISK"
        )

    elif level == "HIGH":

        st.warning(
            "🟠 HIGH CHURN RISK"
        )

    elif level == "MODERATE":

        st.warning(
            "🟡 MODERATE CHURN RISK"
        )

    else:

        st.success(
            "🟢 LOW CHURN RISK"
        )


# =========================================================
# SCORE BREAKDOWN
# =========================================================

def display_score_breakdown(
    result
):

    st.markdown(
        "### 📊 Risk Score Breakdown"
    )

    breakdown = result.get(
        "score_breakdown",
        {}
    )

    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    with col1:

        st.metric(
            "Sentiment",
            f"+{breakdown.get('sentiment', 0)}"
        )

    with col2:

        st.metric(
            "Emotion",
            f"+{breakdown.get('emotion', 0)}"
        )

    with col3:

        st.metric(
            "Dissatisfaction",
            f"+{breakdown.get('dissatisfaction', 0)}"
        )

    with col4:

        st.metric(
            "Severity",
            f"+{breakdown.get('severity', 0)}"
        )

    with col5:

        st.metric(
            "Closure Intent",
            f"+{breakdown.get('closure_intent', 0)}"
        )


# =========================================================
# RISK FACTORS
# =========================================================

def display_risk_factors(
    result
):

    st.markdown(
        "### ⚠️ Risk Factors"
    )

    factors = result.get(
        "risk_factors",
        []
    )

    if not factors:

        st.info(
            "No significant churn risk factors detected."
        )

        return

    for factor in factors:

        st.write(
            f"✓ {factor}"
        )


# =========================================================
# TRIGGERED RULES
# =========================================================

def display_triggered_rules(
    result
):

    st.markdown(
        "### 📋 Triggered Retention Rules"
    )

    rules = result.get(
        "triggered_rules",
        []
    )

    if not rules:

        st.info(
            "No retention rules were triggered."
        )

        return

    for rule in rules:

        priority = rule.get(
            "priority",
            "N/A"
        )

        name = rule.get(
            "name",
            "Unknown Rule"
        )

        reason = rule.get(
            "reason",
            ""
        )

        if priority == "CRITICAL":

            st.error(
                f"🔴 {name} — {priority}"
            )

        elif priority == "HIGH":

            st.warning(
                f"🟠 {name} — {priority}"
            )

        elif priority == "MEDIUM":

            st.info(
                f"🟡 {name} — {priority}"
            )

        else:

            st.info(
                f"🔵 {name} — {priority}"
            )

        if reason:

            st.caption(
                f"Reason: {reason}"
            )


# =========================================================
# RECOMMENDATIONS
# =========================================================

def display_recommendations(
    result
):

    st.markdown(
        "### 🚨 Recommended Recovery Actions"
    )

    recommendations = result.get(
        "recommendations",
        []
    )

    if not recommendations:

        st.success(
            "No recovery actions required."
        )

        return

    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):

        st.write(
            f"**{index}.** {recommendation}"
        )

    # -----------------------------------------------------
    # Cross-sell suppression
    # -----------------------------------------------------

    if result.get(
        "cross_sell_suppression",
        False
    ):

        st.error(
            "⛔ CROSS-SELL SUPPRESSION ACTIVE"
        )

        st.warning(
            "Suspend promotional campaigns and "
            "focus only on customer recovery."
        )


# =========================================================
# MAIN
# =========================================================

def run_module6():

    st.header(
        "📈 Churn Risk & Retention Analysis"
    )

    st.caption(
        "Deterministic churn scoring and "
        "rule-based customer recovery recommendations."
    )

    # =====================================================
    # CALLS
    # =====================================================

    calls = (
        get_available_calls()
    )

    if not calls:

        st.warning(
            "No calls are available."
        )

        st.info(
            "Upload a call using Module 1 first."
        )

        return

    call_options = {

        (
            f"{row['file_name']} | "
            f"{row['call_id']}"
        ):
            row["call_id"]

        for row in calls
    }

    selected_call = st.selectbox(
        "Select a call",
        options=list(
            call_options.keys()
        )
    )

    call_id = call_options[
        selected_call
    ]

    st.divider()

    # =====================================================
    # RUN
    # =====================================================

    if not st.button(
        "📊 Calculate Churn Risk & Recommendations",
        type="primary",
        use_container_width=True
    ):

        return

    # =====================================================
    # PROCESS
    # =====================================================

    try:

        with st.spinner(
            "Calculating customer churn risk..."
        ):

            tool = (
                ChurnRiskTool()
            )

            result = (
                tool.run(
                    call_id
                )
            )

        if not result.get(
            "success",
            False
        ):

            st.error(
                "Churn analysis failed."
            )

            st.error(
                result.get(
                    "error",
                    "Unknown error."
                )
            )

            return

        # =================================================
        # DISPLAY
        # =================================================

        display_churn_score(
            result
        )

        st.divider()

        display_score_breakdown(
            result
        )

        st.divider()

        col1, col2 = (
            st.columns(2)
        )

        with col1:

            display_risk_factors(
                result
            )

        with col2:

            st.markdown(
                "### 🎯 Customer Intent"
            )

            if result.get(
                "closure_intent",
                False
            ):

                st.error(
                    "Customer has expressed "
                    "product/account closure intent."
                )

            else:

                st.success(
                    "No explicit closure intent detected."
                )

        st.divider()

        display_triggered_rules(
            result
        )

        st.divider()

        display_recommendations(
            result
        )

        # =================================================
        # DEBUG / DEVELOPMENT
        # =================================================

        with st.expander(
            "🔧 Raw Module 6 Result"
        ):

            st.json(
                result
            )

    except Exception as e:

        st.error(
            "Module 6 execution failed."
        )

        st.exception(e)