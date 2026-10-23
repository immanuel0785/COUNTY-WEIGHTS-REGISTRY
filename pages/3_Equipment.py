import streamlit as st
from src.db import load_all_db_records

st.set_page_config(page_title="Equipment Registry | Nyeri Registry", page_icon="⚖️", layout="wide")
st.title("⚖️ Equipment & Devices Registry Workspace")
st.markdown("*Track verified pumps, digital scales, counter scales, and mass weights across Nyeri County.*")
st.markdown("---")

db_df = load_all_db_records()
if not db_df.empty:
    eq_pumps = db_df['stamped_pumps'].sum() if 'stamped_pumps' in db_df.columns else 0
    eq_scales = db_df['stamped_scales'].sum() if 'stamped_scales' in db_df.columns else 0
    eq_weights = db_df['stamped_weights'].sum() if 'stamped_weights' in db_df.columns else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Stamped Pumps / Nozzles", f"{eq_pumps:,}")
    c2.metric("Total Stamped Scales", f"{eq_scales:,}")
    c3.metric("Total Stamped Mass Weights", f"{eq_weights:,}")

    st.markdown("---")
    st.subheader("📋 Verified Equipment Active Register")
    st.dataframe(db_df[['serial_no', 'trader_name', 'station', 'stamped_pumps', 'stamped_scales', 'stamped_weights', 'date_entry']], use_container_width=True)
else:
    st.info("No stamped equipment entries recorded in central database yet.")
