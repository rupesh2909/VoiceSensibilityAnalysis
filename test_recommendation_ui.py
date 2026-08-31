import streamlit as st

from database.database import get_connection
from module6.recommendation_ui import render_recommendation

st.set_page_config(
    page_title="Recommendation DB Test",
    layout="wide"
)

call_id = "CALL-20260831-3A72AAF1"

with get_connection() as conn:

    row = conn.execute(
        """
        SELECT recommendation_decision
        FROM churn_risk_analysis
        WHERE call_id = ?
        LIMIT 1
        """,
        (call_id,)
    ).fetchone()

if not row:
    st.error("Recommendation not found.")
else:

    import json

    decision = json.loads(
        row["recommendation_decision"]
    )

    st.markdown(
        f"### Existing Call: `{call_id}`"
    )

    render_recommendation(
        decision
    )
