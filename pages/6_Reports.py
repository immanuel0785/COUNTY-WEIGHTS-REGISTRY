import os
import sys

# Add root directory to path so 'src' can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta
import streamlit as st
from src.db import load_all_db_records
from src.reports import generate_pdf_handin_report, number_to_words_kes

st.set_page_config(page_title="Reports | Nyeri Registry", page_icon="📊", layout="wide")

st.title("📊 Daily Field Hand-In Report Workspace")
st.markdown(
    "*Generate daily summaries grouped by inspection centers with"
    " auto-translated figures-to-words for executive Director hand-in.*"
)
st.markdown("---")

report_date = st.date_input(
    "Select Report Date:", value=datetime.today() - timedelta(days=1)
)
report_date_str = report_date.strftime("%Y-%m-%d")

db_records = load_all_db_records()
if not db_records.empty:
  daily_mask = db_records["date_entry"] == report_date_str
  daily_df = db_records[daily_mask]

  st.markdown(f"### 📋 Hand-In Report Summary: `{report_date_str}`")

  d_m1, d_m2, d_m3 = st.columns(3)
  total_inspections_day = len(daily_df)
  total_revenue_day = (
      daily_df["total_amount"].sum()
      if not daily_df.empty and "total_amount" in daily_df.columns
      else 0
  )
  total_pumps_day = (
      daily_df["stamped_pumps"].sum()
      if not daily_df.empty and "stamped_pumps" in daily_df.columns
      else 0
  )
  total_scales_day = (
      daily_df["stamped_scales"].sum()
      if not daily_df.empty and "stamped_scales" in daily_df.columns
      else 0
  )
  total_weights_day = (
      daily_df["stamped_weights"].sum()
      if not daily_df.empty and "stamped_weights" in daily_df.columns
      else 0
  )

  d_m1.metric("Total Inspections Logged", f"{total_inspections_day:,}")
  d_m2.metric("Total Revenue Collected", f"KES {total_revenue_day:,.2f}")
  d_m3.metric(
      "Equipment Stamped",
      f"Pumps: {total_pumps_day} | Scales: {total_scales_day} | Wts:"
      f" {total_weights_day}",
  )

  st.markdown("---")
  st.markdown("### 🏢 Station-Wise Hand-In Summary Table")

  if not daily_df.empty:
    station_summary = (
        daily_df.groupby("station")
        .agg(
            Traders_Count=("trader_name", "count"),
            Total_Fee=("total_amount", "sum"),
            Stamped_Pumps=("stamped_pumps", "sum"),
            Stamped_Scales=("stamped_scales", "sum"),
            Stamped_Weights=("stamped_weights", "sum"),
        )
        .reset_index()
    )

    station_summary.columns = [
        "Inspection Center / Station",
        "No. of Traders",
        "Total Fee Collected (KES)",
        "Stamped Pumps",
        "Stamped Scales",
        "Stamped Weights",
    ]

    st.dataframe(station_summary, use_container_width=True)

    rev_in_words = number_to_words_kes(total_revenue_day)
    st.info(f"📝 **Auto-Translated Total Revenue (in Words):**\n`{rev_in_words}`")

    st.markdown("---")

    pdf_handin_bytes = generate_pdf_handin_report(
        "Insp. Field Officer",
        report_date_str,
        station_summary,
        total_revenue_day,
        total_inspections_day,
        rev_in_words,
    )

    st.download_button(
        label="📥 Download Printable PDF Hand-In Report (.pdf)",
        data=pdf_handin_bytes,
        file_name=f"HandIn_Report_{report_date_str}.pdf",
        mime="application/pdf",
    )
  else:
    st.info(f"No inspection entries recorded in database for {report_date_str}.")
else:
  st.info("No field inspection records logged in database yet.")
