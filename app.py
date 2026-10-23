import streamlit as st
from src.db import init_db

# Initialize Database on Startup
init_db()

st.set_page_config(
    page_title="County Government of Nyeri | Digital Registry",
    page_icon="⚖️",
    layout="wide",
)

st.switch_page("pages/1_Dashboard.py")
