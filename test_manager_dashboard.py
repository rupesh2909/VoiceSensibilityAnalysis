import streamlit as st

from module6.manager_dashboard import (
    render_manager_dashboard
)

st.set_page_config(
    page_title="Manager Dashboard",
    layout="wide"
)

st.title("Manager Retention Dashboard")

render_manager_dashboard()
