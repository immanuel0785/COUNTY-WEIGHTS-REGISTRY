import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="County Government of Nyeri | Digital Registry",
    page_icon="⚖️",
    layout="wide",
)

# --- OFFICIAL NYERI COUNTY CUSTOM CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117 !important; color: #e6edf3 !important; }
    .dashboard-header-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .db-card {
        background: linear-gradient(90deg, #0d1117 0%, #162419 50%, #0d1117 100%);
        border: 1px solid #2ea043; border-radius: 12px; padding: 18px; text-align: center; margin-top: 20px;
    }
    .flow-arrow { text-align: center; font-size: 20px; color: #2ea043; margin: 8px 0; }
    .nyeri-top-bar {
        background: linear-gradient(90deg, #006837 0%, #0056B3 100%);
        color: white; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px;
        display: flex; align-items: center; justify-content: space-between; font-weight: bold;
    }
    div.stButton > button {
        width: 100% !important; background-color: #161b22 !important; color: #ffffff !important;
        border: 1px solid #30363d !important; border-left: 5px solid #006837 !important;
        border-radius: 8px !important; padding: 16px !important; text-align: left !important;
        font-size: 15px !important; font-weight: bold !important;
    }
    div.stButton > button:hover { background-color: #21262d !important; border-color: #2ea043 !important; color: #2ea043 !important; }
</style>
""", unsafe_allow_html=True)

# Top Official County Banner
st.markdown("""
<div class="nyeri-top-bar">
    <span>⚖️ COUNTY GOVERNMENT OF NYERI</span>
    <span>Department of Trade, Tourism & Co-operative Development</span>
</div>
""", unsafe_allow_html=True)

# Main Header Card
st.markdown("""
<div class="dashboard-header-card">
    <div style="font-size: 28px; margin-bottom: 5px;">🎛️</div>
    <div style="font-size: 22px; font-weight: 700; color: #ffffff;">Nyeri Weights & Measures Digital Registry</div>
    <div style="font-size: 14px; color: #8b949e; margin-top: 4px;">Secure application with role-based access</div>
</div>
<div class="flow-arrow">↓ Select module using the sidebar navigation menu on the left</div>
""", unsafe_allow_html=True)

# 6 Structured Module Navigation Cards (Using st.page_link to prevent path errors)
col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/2_Traders.py", label="👥 Trader Registry - Businesses and contacts", icon="👥")
    st.page_link("pages/4_Inspections.py", label="📋 Inspections - Visits and verification history", icon="📋")
    st.page_link("pages/6_Reports.py", label="📊 Reports - Periodic summaries and exports", icon="📊")

with col2:
    st.page_link("pages/3_Equipment.py", label="⚖️ Equipment Registry - Equipment IDs and status", icon="⚖️")
    st.page_link("pages/5_Fees_and_Payments.py", label="💳 Fee Records - Assessments and reconciled payments", icon="💳")
    st.page_link("pages/7_Administration.py", label="🛡️ Audit & Administration - Users and permissions", icon="🛡️")

# Central Database Footer Card
st.markdown("""
<div class="flow-arrow">↓</div>
<div class="db-card">
    <div style="font-size: 24px; margin-bottom: 5px;">🛢️</div>
    <div style="font-size: 18px; font-weight: 700; color: #2ea043;">Central Database</div>
    <div style="font-size: 13px; color: #8b949e; margin-top: 4px;">Validated records, persistent storage and controlled access</div>
</div>
""", unsafe_allow_html=True)
