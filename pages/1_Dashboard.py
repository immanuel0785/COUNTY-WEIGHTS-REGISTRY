import streamlit as st

st.set_page_config(page_title="Dashboard | Nyeri Registry", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117 !important; color: #e6edf3 !important; }
    .dashboard-header-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 15px;
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
</style>
<div class="nyeri-top-bar">
    <span>⚖️ COUNTY GOVERNMENT OF NYERI</span>
    <span>Department of Trade, Tourism & Co-operative Development</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="dashboard-header-card">
    <div style="font-size: 28px; margin-bottom: 5px;">🎛️</div>
    <div style="font-size: 22px; font-weight: 700; color: #ffffff;">Nyeri Weights & Measures Digital Registry</div>
    <div style="font-size: 14px; color: #8b949e; margin-top: 4px;">Secure application with role-based access</div>
</div>
<div class="flow-arrow">↓ Select module from sidebar or cards below</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("👥 Trader Registry\n\nBusinesses and contacts", use_container_width=True):
        st.switch_page("pages/2_Traders.py")
    if st.button("📋 Inspections\n\nVisits and verification history", use_container_width=True):
        st.switch_page("pages/4_Inspections.py")
    if st.button("📊 Reports\n\nPeriodic summaries and exports", use_container_width=True):
        st.switch_page("pages/6_Reports.py")

with col2:
    if st.button("⚖️ Equipment Registry\n\nEquipment IDs and status", use_container_width=True):
        st.switch_page("pages/3_Equipment.py")
    if st.button("💳 Fee Records\n\nAssessments and reconciled payments", use_container_width=True):
        st.switch_page("pages/5_Fees_and_Payments.py")
    if st.button("🛡️ Audit & Administration\n\nUsers, permissions and change history", use_container_width=True):
        st.switch_page("pages/7_Administration.py")

st.markdown("""
<div class="flow-arrow">↓</div>
<div class="db-card">
    <div style="font-size: 24px; margin-bottom: 5px;">🛢️</div>
    <div style="font-size: 18px; font-weight: 700; color: #2ea043;">Central Database</div>
    <div style="font-size: 13px; color: #8b949e; margin-top: 4px;">Validated records, persistent storage and controlled access</div>
</div>
""", unsafe_allow_html=True)
