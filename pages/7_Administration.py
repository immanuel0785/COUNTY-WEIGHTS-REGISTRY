import streamlit as st
import pandas as pd
from src.db import load_all_db_records, load_traders_from_db

st.set_page_config(page_title="Audit & Admin | Nyeri Registry", page_icon="⚖️", layout="wide")
st.title("🛡️ Audit & Administration Workspace")
st.markdown("*Executive auditing metrics, financial summaries, staff access controls, and change log history.*")
st.markdown("---")

db_records = load_all_db_records()
traders_reg = load_traders_from_db()

total_audited_revenue = pd.to_numeric(db_records['total_amount'], errors='coerce').sum() if not db_records.empty else 0
total_audited_inspections = len(db_records) if not db_records.empty else 0
total_registered_businesses = len(traders_reg) if not traders_reg.empty else 0

a_col1, a_col2, a_col3 = st.columns(3)
a_col1.metric("Total County Revenue Audited", f"KES {total_audited_revenue:,.2f}")
a_col2.metric("Total Inspections Logged", f"{total_audited_inspections:,}")
a_col3.metric("Registered Businesses", f"{total_registered_businesses:,}")

st.markdown("---")
st.markdown("### 📈 Revenue & Inspection Volume by Sub-County")

if not db_records.empty and 'station' in db_records.columns:
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("**Revenue Collected per Station (KES)**")
        station_rev = db_records.groupby('station')['total_amount'].sum()
        st.bar_chart(station_rev)
    with col_v2:
        st.markdown("**Inspection Volume per Station**")
        station_vol = db_records.groupby('station').size()
        st.bar_chart(station_vol)
else:
    st.info("Insufficient inspection records in database to render charts.")

st.markdown("---")
st.markdown("### 👥 Staff Authentication & Permissions Directory")
staff_data = pd.DataFrame({
    "Staff ID": ["NYR_ADMIN_001", "NYR_INSP_042", "NYR_INSP_018"],
    "Officer Name": ["Director of Trade", "Insp. Mwangi", "Insp. Ndirangu"],
    "Role": ["County Administrator", "Senior Field Inspector", "Field Inspector"],
    "Assigned Station": ["All Sub-Counties", "Karatina / Mathira East", "Othaya Town"],
    "Status": ["Active", "Active", "Active"]
})
st.dataframe(staff_data, use_container_width=True)

st.markdown("---")
st.markdown("### 📋 Complete System Audit Trail & Change Log")
if not db_records.empty:
    st.dataframe(db_records, use_container_width=True)
else:
    st.info("No audit log entries recorded in central database yet.")
