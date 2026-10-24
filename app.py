import streamlit as st
from src.db import init_db

# Initialize database on startup
init_db()

st.set_page_config(
    page_title="County Government of Nyeri | Digital Registry",
    page_icon="⚖️",
    layout="wide",
)

# Define official pages using st.Page
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🎛️", default=True)
traders_page = st.Page("pages/2_Traders.py", title="Trader Registry", icon="👥")
equipment_page = st.Page("pages/3_Equipment.py", title="Equipment Registry", icon="⚖️")
inspections_page = st.Page("pages/4_Inspections.py", title="Inspections", icon="📋")
fees_page = st.Page("pages/5_Fees_and_Payments.py", title="Fee Records", icon="💳")
reports_page = st.Page("pages/6_Reports.py", title="Reports", icon="📊")
admin_page = st.Page("pages/7_Administration.py", title="Audit & Administration", icon="🛡️")

# Set up navigation structure
pg = st.navigation({
    "Nyeri Digital Registry": [
        dashboard_page,
        traders_page,
        equipment_page,
        inspections_page,
        fees_page,
        reports_page,
        admin_page
    ]
})

pg.run()
