import streamlit as st
import pandas as pd
from src.db import load_all_db_records

st.set_page_config(page_title="Fees & Payments | Nyeri Registry", page_icon="⚖️", layout="wide")
st.title("💳 Fee Records & Payment Reconciliation Workspace")
st.markdown("*Audited financial ledger records, M-Pesa code tracking, and county revenue reconciliations.*")
st.markdown("---")

db_all = load_all_db_records()
if not db_all.empty:
    total_rev = pd.to_numeric(db_all['total_amount'], errors='coerce').sum()
    st.metric("Total Reconciled County Revenue", f"KES {total_rev:,.2f}")
    st.markdown("---")
    st.subheader("📋 Audited Financial Transactions Log")
    st.dataframe(db_all, use_container_width=True)
else:
    st.info("No payment transactions recorded in central database yet.")
