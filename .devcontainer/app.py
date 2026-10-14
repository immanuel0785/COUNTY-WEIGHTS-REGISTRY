#!/usr/bin/env python
# coding: utf-8

# In[1]:


from datetime import datetime, timedelta
import io
import numpy as np
import pandas as pd
from reportlab.pdfgen import canvas
import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="County Weights & Measures Digital Registry",
    page_icon="⚖️",
    layout="wide",
)


# --- 1. GENERATE SIMULATED HISTORICAL DATA (2015 - 2026) ---
@st.cache_data
def load_mock_data():
  np.random.seed(42)
  n_rows = 4500

  years = np.random.choice(
      range(2015, 2027),
      size=n_rows,
      p=[0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.05],
  )
  traders = [f"Trader_{np.random.randint(1000, 9999)}" for _ in range(n_rows)]
  sub_counties = np.random.choice(
      ["Central Ward", "North Sub-County", "South Market", "East Division"],
      size=n_rows,
  )
  equipment = np.random.choice(
      [
          "Counter Scale",
          "Platform Scale",
          "Fuel Dispenser",
          "Spring Balance",
          "Mass Piece",
      ],
      size=n_rows,
      p=[0.4, 0.2, 0.15, 0.15, 0.1],
  )
  status = np.random.choice(
      ["Passed", "Rejected", "Conditional Pass"], size=n_rows, p=[0.72, 0.20, 0.08]
  )
  fees = np.where(
      status == "Passed",
      np.random.choice([1500, 3000, 5000], size=n_rows),
      np.random.choice([500, 1000], size=n_rows),
  )
  mpesa_codes = [
      f"QHX{np.random.randint(10000, 99999)}" for _ in range(n_rows)
  ]
  next_due = [
      (
          datetime.now() + timedelta(days=np.random.randint(30, 365))
      ).strftime("%Y-%m-%d")
      for _ in range(n_rows)
  ]

  df = pd.DataFrame({
      "Year": years,
      "Trader_Name": traders,
      "Sub_County": sub_counties,
      "Equipment_Type": equipment,
      "Inspection_Status": status,
      "Fee_Collected": fees,
      "Mpesa_Code": mpesa_codes,
      "Next_Due_Date": next_due,
  })
  return df


# Initialize Session State so added entries persist across actions
if "df" not in st.session_state:
  st.session_state["df"] = load_mock_data()

df = st.session_state["df"]


# --- 2. PDF RECEIPT GENERATOR FUNCTION ---
def generate_pdf_receipt(r):
  buffer = io.BytesIO()
  # Standard thermal receipt canvas width (226 points) & height (420 points)
  c = canvas.Canvas(buffer, pagesize=(226, 420))
  c.setFont("Courier-Bold", 10)

  y = 405
  c.drawCentredString(113, y, "COUNTY GOV OF NYERI")
  y -= 12
  c.setFont("Courier", 8)
  c.drawCentredString(113, y, "WEIGHTS & MEASURES DIVISION")
  y -= 14
  c.drawString(15, y, "-" * 38)
  y -= 12

  c.setFont("Courier-Bold", 8)
  c.drawString(15, y, "CERTIFICATE OF VERIFICATION")
  y -= 14
  c.setFont("Courier", 8)
  c.drawString(15, y, f"Receipt No: NYR-{r['code']}")
  y -= 12
  c.drawString(15, y, f"Date Issued: {r['date']}")
  y -= 12
  c.drawString(15, y, f"Business: {r['trader']}")
  y -= 12
  c.drawString(15, y, f"Phone: {r['phone']}")
  y -= 12
  c.drawString(15, y, f"Sub-County: {r['subcounty']}")
  y -= 12
  c.drawString(15, y, f"Equipment: {r['equipment']}")
  y -= 12
  c.drawString(15, y, f"Status: {r['status']}")
  y -= 14
  c.drawString(15, y, "-" * 38)
  y -= 12

  c.drawString(15, y, f"Stamping Fee: KES {r['fee']:,}")
  y -= 12
  c.drawString(15, y, f"M-Pesa Ref: {r['code']}")
  y -= 12
  c.drawString(15, y, f"Next Due: {r['due']}")
  y -= 14
  c.drawString(15, y, "-" * 38)
  y -= 14

  c.drawCentredString(113, y, "Authorized Inspector")
  y -= 10
  c.drawCentredString(113, y, "*** OFFICIAL DIGITAL RECORD ***")

  c.showPage()
  c.save()
  buffer.seek(0)
  return buffer.getvalue()


# --- 3. SIDEBAR FILTERS (The Control Panel) ---
st.sidebar.header("🔍 Registry Filter Controls")

selected_years = st.sidebar.slider(
    "Select Year Range", 2015, 2026, (2015, 2026)
)
selected_subcounty = st.sidebar.selectbox(
    "Filter by Region", ["All"] + list(df["Sub_County"].unique())
)
selected_status = st.sidebar.selectbox(
    "Compliance Status", ["All"] + list(df["Inspection_Status"].unique())
)

# Apply filters
filtered_df = df[
    (df["Year"] >= selected_years[0]) & (df["Year"] <= selected_years[1])
]
if selected_subcounty != "All":
  filtered_df = filtered_df[filtered_df["Sub_County"] == selected_subcounty]
if selected_status != "All":
  filtered_df = filtered_df[filtered_df["Inspection_Status"] == selected_status]

# --- 4. MAIN DASHBOARD HEADER ---
st.title("⚖️ County Weights & Measures Digital Transformation Hub")
st.markdown(
    "*Replacing manual paper records with real-time analytics, duplicate"
    " prevention, and cashless M-Pesa revenue tracking.*"
)
st.markdown("---")

# --- 5. TOP-LEVEL METRICS (KPIs) ---
total_inspections = len(filtered_df)
total_revenue = filtered_df["Fee_Collected"].sum()
compliance_rate = (
    (
        len(filtered_df[filtered_df["Inspection_Status"] == "Passed"])
        / total_inspections
        * 100
    )
    if total_inspections > 0
    else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("Total Inspections Logged", f"{total_inspections:,}")
col2.metric("Estimated Revenue Collected", f"KES {total_revenue:,.2f}")
col3.metric("Compliance Rate", f"{compliance_rate:.1f}%")

st.markdown("---")

# --- 6. TABS FOR ORGANIZED NAVIGATION ---
tab1, tab2, tab3 = st.tabs([
    "📈 Trends & Analytics",
    "📂 Digital Archive (Search)",
    "📝 Field Inspection Portal (Cashless)",
])

with tab1:
  st.subheader("Historical Inspection & Revenue Growth")

  col_a, col_b = st.columns(2)

  with col_a:
    st.markdown("**Inspections per Year**")
    yearly_counts = filtered_df.groupby("Year").size()
    st.bar_chart(yearly_counts)

  with col_b:
    st.markdown("**Revenue Collected per Year (KES)**")
    yearly_revenue = filtered_df.groupby("Year")["Fee_Collected"].sum()
    st.line_chart(yearly_revenue)

with tab2:
  st.subheader("Master Database Lookup (Replaces Physical Books)")
  search_query = st.text_input(
      "Search Trader Name or M-Pesa Code:",
      placeholder="Type trader name or code...",
  )

  display_df = filtered_df
  if search_query:
    display_df = display_df[
        display_df["Trader_Name"].str.contains(search_query, case=False, na=False)
        | display_df["Mpesa_Code"].str.contains(search_query, case=False, na=False)
    ]

  st.dataframe(display_df, use_container_width=True)
  st.caption(f"Showing {len(display_df)} matching records.")

  csv_master = display_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export Filtered Audit Report (CSV)",
      data=csv_master,
      file_name="county_weights_audit_report.csv",
      mime="text/csv",
  )

with tab3:
  st.subheader("Simulate New Field Entry & M-Pesa Payment")
  st.markdown(
      "All inspection fees are strictly cashless via M-Pesa. The system"
      " automatically runs duplicate checks and computes annual recertification"
      " dates."
  )

  if "last_receipt_data" not in st.session_state:
    st.session_state["last_receipt_data"] = None

  with st.form("inspection_form"):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
      new_trader = st.text_input("Trader / Business Name")
      new_equipment = st.selectbox(
          "Equipment Type",
          [
              "Counter Scale",
              "Platform Scale",
              "Fuel Dispenser",
              "Spring Balance",
              "Mass Piece",
          ],
      )
      phone_number = st.text_input(
          "Trader Phone Number (M-Pesa)", placeholder="0712345678"
      )
    with f_col2:
      new_subcounty = st.selectbox(
          "Sub-County",
          ["Central Ward", "North Sub-County", "South Market", "East Division"],
      )
      new_status = st.selectbox(
          "Inspection Result", ["Passed", "Rejected", "Conditional Pass"]
      )
      inspection_date_obj = st.date_input(
          "Inspection Date", value=datetime.today()
      )
      mpesa_code = st.text_input(
          "M-Pesa Confirmation Code", placeholder="e.g., QHC792XKL1"
      )

    submitted = st.form_submit_button("Verify Payment & Submit Digital Record")

    if submitted:
      clean_code = mpesa_code.strip().upper()
      if new_trader.strip() == "":
        st.warning("Please enter a valid Trader / Business Name.")
      elif len(clean_code) < 8:
        st.error(
            "⚠️ Transaction Blocked: A valid M-Pesa confirmation code is"
            " required (Strictly No Cash Allowed)."
        )
      elif clean_code in st.session_state["df"]["Mpesa_Code"].values:
        st.error(
            f"🚨 FRAUD ALERT: M-Pesa code **{clean_code}** has already been"
            " used for a previous inspection! Code reuse is strictly locked."
        )
      else:
        fee_amount = 3000 if new_status == "Passed" else 1000
        inspection_date_str = inspection_date_obj.strftime("%Y-%m-%d")
        extracted_year = inspection_date_obj.year
        next_due_str = (inspection_date_obj + timedelta(days=365)).strftime(
            "%Y-%m-%d"
        )

        new_row = pd.DataFrame({
            "Year": [extracted_year],
            "Trader_Name": [new_trader],
            "Sub_County": [new_subcounty],
            "Equipment_Type": [new_equipment],
            "Inspection_Status": [new_status],
            "Fee_Collected": [fee_amount],
            "Mpesa_Code": [clean_code],
            "Next_Due_Date": [next_due_str],
        })

        st.session_state["df"] = pd.concat(
            [st.session_state["df"], new_row], ignore_index=True
        )

        st.session_state["last_receipt_data"] = {
            "trader": new_trader,
            "phone": phone_number,
            "subcounty": new_subcounty,
            "equipment": new_equipment,
            "status": new_status,
            "fee": fee_amount,
            "code": clean_code,
            "date": inspection_date_str,
            "due": next_due_str,
        }
        st.success(
            f"Payment of KES {fee_amount:,} verified via M-Pesa code"
            f" **{clean_code}**! Record logged to database."
        )

  # --- DISPLAY SUPERMARKET-STYLE PREVIEW CARD & PDF DOWNLOAD ---
  if st.session_state["last_receipt_data"] is not None:
    r = st.session_state["last_receipt_data"]
    st.markdown("---")
    st.subheader("🧾 Official Certificate of Verification (Receipt Preview)")

    receipt_html = f"""
        <style>
        .receipt-box {{
            border: 2px dashed #333;
            padding: 20px;
            font-family: 'Courier New', Courier, monospace;
            background-color: #fafafa;
            color: #111;
            max-width: 450px;
            margin: auto;
            border-radius: 6px;
        }}
        .receipt-header {{
            text-align: center;
            font-weight: bold;
        }}
        </style>

        <div class="receipt-box">
            <div class="receipt-header">
                <p style="margin:0; font-size:16px;"><b>COUNTY GOVERNMENT OF NYERI</b></p>
                <p style="margin:0; font-size:12px;">DEPARTMENT OF TRADE & CO-OPERATIVES</p>
                <p style="margin:0; font-size:12px;"><b>WEIGHTS & MEASURES DIVISION</b></p>
                <p>----------------------------------------</p>
            </div>
            <p style="margin:4px 0;"><b>Certificate No:</b> NYR-WM-{r['code']}</p>
            <p style="margin:4px 0;"><b>Date Issued:</b> {r['date']}</p>
            <p>----------------------------------------</p>
            <p style="margin:4px 0;"><b>Business Name:</b> {r['trader']}</p>
            <p style="margin:4px 0;"><b>Phone Contact:</b> {r['phone']}</p>
            <p style="margin:4px 0;"><b>Sub-County:</b> {r['subcounty']}</p>
            <p style="margin:4px 0;"><b>Equipment Type:</b> {r['equipment']}</p>
            <p style="margin:4px 0;"><b>Inspection Status:</b> <b>{r['status']}</b></p>
            <p>----------------------------------------</p>
            <p style="margin:4px 0;"><b>Stamping Fee Paid:</b> KES {r['fee']:,}</p>
            <p style="margin:4px 0;"><b>M-Pesa Reference:</b> {r['code']}</p>
            <p style="margin:4px 0; color: #b22222;"><b>Next Verification Due:</b> {r['due']}</p>
            <p>----------------------------------------</p>
            <div class="receipt-header">
                <p style="margin:0; font-size:11px;"><i>Status: Verified & Synced to County Server</i></p>
                <p style="margin:0; font-size:10px;">*** OFFICIAL DIGITAL STAMP ***</p>
            </div>
        </div>
        """
    st.markdown(receipt_html, unsafe_allow_html=True)

    # Generate PDF bytes
    pdf_bytes = generate_pdf_receipt(r)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Official Receipt (PDF)",
        data=pdf_bytes,
        file_name=f"Certificate_{r['trader']}_{r['code']}.pdf",
        mime="application/pdf",
    )


# In[ ]:




