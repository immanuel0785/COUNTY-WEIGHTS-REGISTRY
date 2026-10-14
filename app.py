from datetime import datetime, timedelta
import io
import numpy as np
import pandas as pd
from reportlab.pdfgen import canvas
import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="County Government of Nyeri | Weights & Measures Registry",
    page_icon="⚖️",
    layout="wide",
)

# --- 0. OFFICIAL NYERI COUNTY CUSTOM CSS STYLING ---
nyeri_custom_css = """
<style>
    /* Nyeri Brand Palette: 
       Green (#006837), Sky Blue (#0056B3), Ochre Earth (#8B4513) */

    /* Primary Headers in Nyeri Forest Green */
    h1, h2, h3 {
        color: #006837 !important;
        font-weight: 700 !important;
    }

    /* Style Primary Form Buttons in Nyeri Forest Green */
    div.stButton > button:first-child {
        background-color: #006837 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #004d28 !important;
        color: #FFD700 !important; /* Gold highlight on hover */
    }

    /* Sidebar Background - Nyeri Dark Navy/Blue Accent */
    section[data-testid="stSidebar"] {
        background-color: #0B192C !important;
    }

    /* Metric Value Styling */
    div[data-testid="stMetricValue"] {
        color: #006837 !important;
        font-weight: bold !important;
    }

    /* Tab Selected Styling */
    button[aria-selected="true"] {
        border-bottom-color: #006837 !important;
        color: #006837 !important;
        font-weight: bold !important;
    }

    /* County Banner Badge */
    .nyeri-banner {
        background: linear-gradient(90deg, #006837 0%, #0056B3 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .nyeri-banner h4 {
        color: white !important;
        margin: 0;
    }
</style>
"""
st.markdown(nyeri_custom_css, unsafe_allow_html=True)


# --- 1. SECURE GOVERNMENT AUTHENTICATION GATE ---
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
  st.markdown(
      """
    <div class="nyeri-banner">
        <h4>⚖️ COUNTY GOVERNMENT OF NYERI</h4>
        <span>Department of Trade, Tourism & Co-operative Development</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  st.subheader("Weights & Measures Digital Registry - Staff Portal Access")
  st.markdown(
      "Restricted Government System. Authorized personnel only. Please enter"
      " your staff credentials to proceed."
  )

  with st.form("login_form"):
    username = st.text_input(
        "Staff / Inspector ID", placeholder="e.g., NYR_INSP_042"
    )
    password = st.text_input("Secure PIN / Password", type="password")
    login_btn = st.form_submit_button("Authenticate & Enter Portal")

    if login_btn:
      if username.strip().upper().startswith("NYR_") and len(password) >= 4:
        st.session_state["authenticated"] = True
        st.success("Access Granted. Loading secure Nyeri County registry...")
        st.rerun()
      else:
        st.error(
            "⚠️ Authentication Failed: Invalid Staff ID or secure PIN. (Demo"
            " hint: Use ID starting with 'NYR_' and a 4+ digit PIN)"
        )

  st.stop()


# --- 2. GENERATE SIMULATED HISTORICAL DATA (2015 - 2026) ---
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


if "df" not in st.session_state:
  st.session_state["df"] = load_mock_data()

df = st.session_state["df"]


# --- 3. PDF RECEIPT GENERATOR FUNCTION ---
def generate_pdf_receipt(r):
  buffer = io.BytesIO()
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


# --- 4. SIDEBAR FILTERS & CONTROL PANEL ---
st.sidebar.header("🔍 Registry Controls")

if st.sidebar.button("🔒 Secure Logout"):
  st.session_state["authenticated"] = False
  st.rerun()

selected_years = st.sidebar.slider(
    "Select Year Range", 2015, 2026, (2015, 2026)
)
selected_subcounty = st.sidebar.selectbox(
    "Filter by Sub-County", ["All"] + list(df["Sub_County"].unique())
)
selected_status = st.sidebar.selectbox(
    "Compliance Status", ["All"] + list(df["Inspection_Status"].unique())
)

filtered_df = df[
    (df["Year"] >= selected_years[0]) & (df["Year"] <= selected_years[1])
]
if selected_subcounty != "All":
  filtered_df = filtered_df[filtered_df["Sub_County"] == selected_subcounty]
if selected_status != "All":
  filtered_df = filtered_df[filtered_df["Inspection_Status"] == selected_status]

# --- 5. MAIN DASHBOARD HEADER WITH OFFICIAL NYERI BANNER ---
st.markdown(
    """
<div class="nyeri-banner">
    <h4>COUNTY GOVERNMENT OF NYERI | DEPARTMENT OF TRADE</h4>
    <span>Official Weights & Measures Digital Portal</span>
</div>
""",
    unsafe_allow_html=True,
)

st.title("⚖️ Digital Verification & Audit Hub")
st.markdown(
    "*Replacing manual paper logbooks with automated fraud prevention, real-time analytics, and cashless revenue management.*"
)
st.markdown("---")

# --- 6. TOP-LEVEL METRICS (KPIs) ---
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
col2.metric("Revenue Collected", f"KES {total_revenue:,.2f}")
col3.metric("Compliance Rate", f"{compliance_rate:.1f}%")

st.markdown("---")

# --- 7. TABS FOR ORGANIZED NAVIGATION ---
tab1, tab2, tab3 = st.tabs([
    "📈 Revenue & Compliance Trends",
    "📂 Digital Archive (Search & Export)",
    "📝 Field Inspection Portal (M-Pesa Verified)",
])

with tab1:
  st.subheader("Historical Verification Performance")
  col_a, col_b = st.columns(2)

  with col_a:
    st.markdown("**Inspections Conducted per Year**")
    yearly_counts = filtered_df.groupby("Year").size()
    st.bar_chart(yearly_counts)

  with col_b:
    st.markdown("**Revenue Collected per Year (KES)**")
    yearly_revenue = filtered_df.groupby("Year")["Fee_Collected"].sum()
    st.line_chart(yearly_revenue)

with tab2:
  st.subheader("Master Verification Registry")
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
  st.caption(f"Displaying {len(display_df)} official records.")

  csv_master = display_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export Filtered Audit Report (CSV)",
      data=csv_master,
      file_name="nyeri_county_weights_report.csv",
      mime="text/csv",
  )

with tab3:
  st.subheader("Log Field Verification & Cashless Receipt")
  st.markdown(
      "All stamping fees are strictly processed via M-Pesa. System"
      " automatically checks for code reuse and calculates 1-year"
      " re-verification due dates."
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
