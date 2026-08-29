import streamlit as st

from module7.dashboard_service import (
    DashboardService
)


# =========================================================
# HELPERS
# =========================================================

def priority_icon(
    priority
):

    if priority == "CRITICAL":
        return "🔴"

    if priority == "HIGH":
        return "🟠"

    if priority == "MEDIUM":
        return "🟡"

    return "🟢"


def risk_icon(
    level
):

    if level == "CRITICAL":
        return "🔴"

    if level == "HIGH":
        return "🟠"

    if level == "MODERATE":
        return "🟡"

    return "🟢"


# =========================================================
# CUSTOMER PROFILE
# =========================================================

def display_customer_profile(
    service,
    customer_id
):

    customer = (
        service.get_customer(
            customer_id
        )
    )

    if not customer:

        st.warning(
            "Customer profile not found."
        )

        return

    st.markdown(
        "## 👤 Customer Profile"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Customer",
            customer.get(
                "customer_name"
            ) or "Unknown"
        )

    with col2:

        st.metric(
            "Segment",
            customer.get(
                "customer_segment"
            ) or "N/A"
        )

    with col3:

        st.metric(
            "Customer Value",
            customer.get(
                "customer_value"
            ) or "N/A"
        )

    history = (
        service.get_customer_history(
            customer_id
        )
    )

    with col4:

        st.metric(
            "Total Calls",
            len(history)
        )

    st.markdown(
        "### 📞 Customer Call History"
    )

    if not history:

        st.info(
            "No call history available."
        )

        return

    for call in history:

        risk = call.get(
            "churn_risk_level"
        )

        title = (
            f"{priority_icon(call.get('recovery_priority'))} "
            f"{call.get('file_name')} "
            f"— {call.get('created_at', '')[:19]}"
        )

        with st.expander(
            title
        ):

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                st.write(
                    "**Sentiment:**",
                    call.get(
                        "sentiment"
                    ) or "N/A"
                )

                st.write(
                    "**Emotion:**",
                    call.get(
                        "primary_emotion"
                    ) or "N/A"
                )

            with col2:

                st.write(
                    "**Root Cause:**",
                    call.get(
                        "root_cause_category"
                    ) or "N/A"
                )

                st.write(
                    "**Severity:**",
                    call.get(
                        "severity"
                    ) or "N/A"
                )

            with col3:

                if call.get(
                    "churn_risk_score"
                ) is not None:

                    st.write(
                        "**Churn Risk:**",
                        f"{call['churn_risk_score']:.0f}/100"
                    )

                st.write(
                    "**Risk Level:**",
                    f"{risk_icon(risk)} {risk or 'N/A'}"
                )


# =========================================================
# MAIN DASHBOARD
# =========================================================

def run_module7():

    st.header(
        "🧑‍💼 Manager Recovery Dashboard"
    )

    st.caption(
        "Prioritized customer recovery queue "
        "using sentiment, emotion, root cause, "
        "churn risk and retention rules."
    )

    service = DashboardService()

    # =====================================================
    # KPI
    # =====================================================

    kpis = (
        service.get_kpis()
    )

    st.markdown(
        "## 📊 Recovery Overview"
    )

    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    with col1:

        st.metric(
            "Customers",
            kpis[
                "total_customers"
            ]
        )

    with col2:

        st.metric(
            "Total Calls",
            kpis[
                "total_calls"
            ]
        )

    with col3:

        st.metric(
            "Analyzed Calls",
            kpis[
                "analyzed_calls"
            ]
        )

    with col4:

        st.metric(
            "Critical Cases",
            kpis[
                "critical_cases"
            ]
        )

    with col5:

        st.metric(
            "Avg Churn Risk",
            f"{kpis['average_risk']:.1f}/100"
        )

    st.divider()

    # =====================================================
    # RECOVERY QUEUE
    # =====================================================

    st.markdown(
        "## 🚨 Prioritized Customer Recovery Queue"
    )

    queue = (
        service.get_recovery_queue()
    )

    if not queue:

        st.success(
            "No analyzed recovery cases available."
        )

        st.info(
            "Run Module 6 on an analyzed call first."
        )

        return

    # -----------------------------------------------------
    # Queue
    # -----------------------------------------------------

    for index, case in enumerate(
        queue,
        start=1
    ):

        priority = case.get(
            "recovery_priority"
        ) or "LOW"

        score = case.get(
            "churn_risk_score"
        ) or 0

        customer_name = (
            case.get(
                "customer_name"
            )
            or "Unknown Customer"
        )

        customer_id = case.get(
            "customer_id"
        )

        title = (
            f"{priority_icon(priority)} "
            f"#{index} — "
            f"{customer_name} "
            f"— Churn Risk {score:.0f}/100"
        )

        if priority == "CRITICAL":

            container = st.error

        elif priority == "HIGH":

            container = st.warning

        else:

            container = st.info

        with st.container(
            border=True
        ):

            container(
                f"{priority_icon(priority)} "
                f"{priority} PRIORITY"
            )

            col1, col2, col3, col4 = (
                st.columns(4)
            )

            with col1:

                st.write(
                    "**Customer**"
                )

                st.write(
                    customer_name
                )

                st.caption(
                    customer_id or "No customer ID"
                )

            with col2:

                st.write(
                    "**Churn Risk**"
                )

                st.metric(
                    "Score",
                    f"{score:.0f}/100"
                )

                st.caption(
                    case.get(
                        "churn_risk_level"
                    ) or "N/A"
                )

            with col3:

                st.write(
                    "**Customer State**"
                )

                st.write(
                    f"Sentiment: "
                    f"{case.get('sentiment') or 'N/A'}"
                )

                st.write(
                    f"Emotion: "
                    f"{case.get('primary_emotion') or 'N/A'}"
                )

            with col4:

                st.write(
                    "**Root Cause**"
                )

                st.write(
                    case.get(
                        "root_cause_category"
                    ) or "N/A"
                )

                st.write(
                    case.get(
                        "severity"
                    ) or "N/A"
                )

            # -------------------------------------------------
            # Intent
            # -------------------------------------------------

            if case.get(
                "closure_intent"
            ):

                st.error(
                    "⚠️ Customer has expressed "
                    "closure / switching intent."
                )

            # -------------------------------------------------
            # Fraud
            # -------------------------------------------------

            if case.get(
                "fraud_intent"
            ):

                st.error(
                    "🚨 Fraud / unauthorized "
                    "transaction intent detected."
                )

            # -------------------------------------------------
            # Actions
            # -------------------------------------------------

            recommendations = case.get(
                "recommendations",
                []
            )

            if recommendations:

                with st.expander(
                    "🎯 Recommended Recovery Actions"
                ):

                    for recommendation in recommendations:

                        st.write(
                            f"• {recommendation}"
                        )

            # -------------------------------------------------
            # Rules
            # -------------------------------------------------

            rules = case.get(
                "triggered_rules",
                []
            )

            if rules:

                with st.expander(
                    "📋 Triggered Retention Rules"
                ):

                    for rule in rules:

                        st.write(
                            f"**{rule.get('name', 'Rule')}** "
                            f"— {rule.get('priority', 'N/A')}"
                        )

                        if rule.get(
                            "reason"
                        ):

                            st.caption(
                                rule["reason"]
                            )

            # -------------------------------------------------
            # Risk Factors
            # -------------------------------------------------

            factors = case.get(
                "risk_factors",
                []
            )

            if factors:

                with st.expander(
                    "⚠️ Risk Factors"
                ):

                    for factor in factors:

                        st.write(
                            f"✓ {factor}"
                        )

            # -------------------------------------------------
            # Customer
            # -------------------------------------------------

            if customer_id:

                if st.button(
                    "👤 View Customer History",
                    key=f"customer_{index}"
                ):

                    st.session_state[
                        "module7_customer_id"
                    ] = customer_id

    st.divider()

    # =====================================================
    # SELECTED CUSTOMER
    # =====================================================

    customer_id = (
        st.session_state.get(
            "module7_customer_id"
        )
    )

    if customer_id:

        display_customer_profile(
            service,
            customer_id
        )