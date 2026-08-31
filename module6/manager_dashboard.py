"""
Module 6 — Manager Retention Dashboard

Presentation layer for manager-facing retention insights.

Business rules remain in retention_rules.py.
Recommendation presentation remains in recommendation_ui.py.
Database access is contained in this module.
"""

import json
import streamlit as st
from textwrap import dedent

from database.database import get_connection
from module6.recommendation_ui import render_recommendation


# =========================================================
# DATABASE
# =========================================================

def get_manager_dashboard_data():
    """
    Retrieve manager dashboard data from SQLite.

    Only analyzed calls are included in the risk population.
    """

    with get_connection() as conn:

        summary = conn.execute(
            """
            SELECT
                COUNT(*) AS analyzed_calls,

                SUM(
                    CASE
                        WHEN churn_risk_level = 'CRITICAL'
                        THEN 1 ELSE 0
                    END
                ) AS critical_calls,

                SUM(
                    CASE
                        WHEN churn_risk_level = 'HIGH'
                        THEN 1 ELSE 0
                    END
                ) AS high_calls,

                SUM(
                    CASE
                        WHEN recovery_priority IN ('CRITICAL', 'HIGH')
                        THEN 1 ELSE 0
                    END
                ) AS recovery_required,

                SUM(
                    CASE
                        WHEN cross_sell_suppression = 1
                        THEN 1 ELSE 0
                    END
                ) AS suppressed_calls

            FROM churn_risk_analysis
            """
        ).fetchone()

        customers = conn.execute(
            """
            SELECT
                c.customer_id,
                c.customer_name,
                c.customer_segment,
                c.customer_value,

                COUNT(DISTINCT cra.call_id)
                    AS analyzed_calls,

                MAX(cra.churn_risk_score)
                    AS max_churn_risk,

                AVG(cra.churn_risk_score)
                    AS avg_churn_risk,

                MAX(cra.churn_risk_level)
                    AS churn_risk_level,

                MAX(cra.recovery_priority)
                    AS recovery_priority,

                SUM(
                    CASE
                        WHEN cra.closure_intent = 1
                        THEN 1 ELSE 0
                    END
                ) AS closure_intent_calls,

                SUM(
                    CASE
                        WHEN cra.cross_sell_suppression = 1
                        THEN 1 ELSE 0
                    END
                ) AS suppressed_calls,

                MAX(cra.created_at)
                    AS latest_analysis

            FROM customers c

            INNER JOIN calls call
                ON call.customer_id = c.customer_id

            INNER JOIN churn_risk_analysis cra
                ON cra.call_id = call.call_id

            GROUP BY
                c.customer_id,
                c.customer_name,
                c.customer_segment,
                c.customer_value

            ORDER BY
                max_churn_risk DESC,
                latest_analysis DESC
            """
        ).fetchall()

        risk_drivers = conn.execute(
            """
            SELECT
                root_cause_category,
                COUNT(*) AS occurrences

            FROM dissatisfaction_root_causes

            WHERE root_cause_category IS NOT NULL

            GROUP BY root_cause_category

            ORDER BY occurrences DESC
            """
        ).fetchall()

        recent_calls = conn.execute(
            """
            SELECT
                cra.call_id,
                c.customer_name,
                c.customer_value,
                cra.churn_risk_score,
                cra.churn_risk_level,
                cra.recovery_priority,
                cra.closure_intent,
                cra.cross_sell_suppression,
                cra.recommendation_decision,
                cra.created_at

            FROM churn_risk_analysis cra

            INNER JOIN calls call
                ON call.call_id = cra.call_id

            INNER JOIN customers c
                ON c.customer_id = call.customer_id

            ORDER BY cra.created_at DESC

            LIMIT 10
            """
        ).fetchall()

    return {
        "summary": dict(summary) if summary else {},
        "customers": [dict(row) for row in customers],
        "risk_drivers": [dict(row) for row in risk_drivers],
        "recent_calls": [dict(row) for row in recent_calls],
    }


# =========================================================
# HELPERS
# =========================================================

def _safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _load_recommendation(value):
    """
    Convert DB JSON representation into a dictionary.
    """

    if isinstance(value, dict):
        return value

    if not value:
        return None

    try:
        result = json.loads(value)

        if isinstance(result, dict):
            return result

    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    return None


# =========================================================
# KPI CARDS
# =========================================================

def render_kpi_cards(summary):

    analyzed_calls = _safe_int(
        summary.get("analyzed_calls")
    )

    critical_calls = _safe_int(
        summary.get("critical_calls")
    )

    high_calls = _safe_int(
        summary.get("high_calls")
    )

    recovery_required = _safe_int(
        summary.get("recovery_required")
    )

    suppressed_calls = _safe_int(
        summary.get("suppressed_calls")
    )

    st.markdown(
        "### 📊 Retention Overview"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Analyzed Calls",
            analyzed_calls
        )

    with col2:
        st.metric(
            "Critical Risk",
            critical_calls
        )

    with col3:
        st.metric(
            "High Risk",
            high_calls
        )

    with col4:
        st.metric(
            "Recovery Required",
            recovery_required
        )

    with col5:
        st.metric(
            "Cross-Sell Suppressed",
            suppressed_calls
        )


# =========================================================
# CUSTOMER ATTENTION CARDS
# =========================================================

def render_customer_attention_cards(customers):

    st.markdown(
        "### 🔥 Customers Requiring Attention"
    )

    if not customers:

        st.info(
            "No analyzed customers require attention yet."
        )

        return

    # -----------------------------------------------------
    # Three customer cards per row
    # -----------------------------------------------------

    for start_index in range(
        0,
        len(customers),
        3
    ):

        row = customers[
            start_index:start_index + 3
        ]

        columns = st.columns(3)

        for column, customer in zip(
            columns,
            row
        ):

            with column:

                priority = (
                    customer.get(
                        "recovery_priority"
                    )
                    or "LOW"
                )

                risk = _safe_float(
                    customer.get(
                        "max_churn_risk"
                    )
                )

                name = (
                    customer.get(
                        "customer_name"
                    )
                    or "Unknown"
                )

                segment = (
                    customer.get(
                        "customer_segment"
                    )
                    or "N/A"
                )

                value = (
                    customer.get(
                        "customer_value"
                    )
                    or "N/A"
                )

                analyzed_calls = _safe_int(
                    customer.get(
                        "analyzed_calls"
                    )
                )

                closure_intents = _safe_int(
                    customer.get(
                        "closure_intent_calls"
                    )
                )

                # -----------------------------------------
                # CARD
                # -----------------------------------------

                with st.container(
                    border=True
                ):

                    st.caption(
                        f"{priority} PRIORITY"
                    )

                    st.subheader(
                        name
                    )

                    st.markdown(
                        f"**{segment}**  •  **{value}**"
                    )

                    st.metric(
                        "Churn Risk",
                        f"{risk:.0f}"
                    )

                    st.caption(
                        f"{analyzed_calls} analyzed calls"
                        f"  •  "
                        f"{closure_intents} closure intents"
                    )


# =========================================================
# RISK DRIVER CARDS
# =========================================================

def render_risk_driver_cards(risk_drivers):

    st.markdown(
        "### ⚠️ Top Risk Drivers"
    )

    if not risk_drivers:

        st.info(
            "No root-cause data available."
        )

        return

    # -----------------------------------------------------
    # Three cards per row
    # -----------------------------------------------------

    for start_index in range(
        0,
        len(risk_drivers),
        3
    ):

        row = risk_drivers[
            start_index:start_index + 3
        ]

        columns = st.columns(3)

        for column, driver in zip(
            columns,
            row
        ):

            with column:

                category = (
                    driver.get(
                        "root_cause_category"
                    )
                    or "Unknown"
                )

                occurrences = _safe_int(
                    driver.get(
                        "occurrences"
                    )
                )

                with st.container(
                    border=True
                ):

                    st.caption(
                        "ROOT CAUSE"
                    )

                    st.subheader(
                        category
                    )

                    st.metric(
                        "Occurrences",
                        occurrences
                    )


# =========================================================
# RECENT ANALYSIS
# =========================================================

def render_recent_analysis(recent_calls):

    st.markdown(
        "### 📋 Recent Customer Analysis"
    )

    if not recent_calls:

        st.info(
            "No churn analyses available yet."
        )

        return

    for call in recent_calls:

        recommendation = _load_recommendation(
            call.get(
                "recommendation_decision"
            )
        )

        customer_name = (
            call.get(
                "customer_name"
            )
            or "Unknown"
        )

        risk = _safe_float(
            call.get(
                "churn_risk_score"
            )
        )

        with st.expander(
            f"{customer_name}  •  "
            f"{call.get('call_id')}  •  "
            f"Risk {risk:.0f}"
        ):

            if recommendation:

                render_recommendation(
                    recommendation
                )

            else:

                st.warning(
                    "Recommendation decision is not available."
                )


# =========================================================
# MAIN DASHBOARD
# =========================================================

def render_manager_dashboard():

    data = (
        get_manager_dashboard_data()
    )

    render_kpi_cards(
        data["summary"]
    )

    st.divider()

    render_customer_attention_cards(
        data["customers"]
    )

    st.divider()

    render_risk_driver_cards(
        data["risk_drivers"]
    )

    st.divider()

    render_recent_analysis(
        data["recent_calls"]
    )
