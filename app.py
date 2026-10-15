from datetime import datetime, timedelta
import io
import time
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
       Forest Green (#006837), Sky Blue (#0056B3), Ochre Earth (#8B4513) */

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

    /* Sidebar Background - Nyeri Dark Navy Accent */
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


# --- 1. SECURE GOVERNMENT AUTHENTICATION GATE & USER ROLES ---
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
  st.session_state["user_name"] = ""
  st.session_state["user_role"] = ""
  st.session_state["user_subcounty"] = ""

VALID_STAFF_DIRECTORY = {
    "NYR_INSP_042": {
        "pin": "4200",
        "name": "Insp. Mwangi",
        "role": "Senior Field Inspector",
        "subcounty": "Karatina / Mathira East",
    },
    "NYR_INSP_018": {
        "pin": "1800",
        "name": "Insp. Ndirangu",
        "role": "Field Inspector",
        "subcounty": "Othaya Town",
    },
    "NYR_ADMIN_001": {
        "pin": "0001",
        "name": "Director of Trade",
        "role": "County Administrator",
        "subcounty": "All Sub-Counties",
    },
}

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
      " your official staff ID and secure PIN."
  )

  st.info(
      "💡 **Demo Login Credentials for Presentation:**\n"
      "• **Administrator:** ID: `NYR_ADMIN_001` | PIN: `0001`\n"
      "• **Karatina Inspector:** ID: `NYR_INSP_042` | PIN: `4200`\n"
      "• **Othaya Inspector:** ID: `NYR_INSP_018` | PIN: `1800`"
  )

  with st.form("login_form"):
    username = st.text_input(
        "Staff / Inspector ID", placeholder="e.g., NYR_ADMIN_001"
    )
    password = st.text_input("Secure PIN / Password", type="password")
    login_btn = st.form_submit_button("Authenticate & Enter Portal")

    if login_btn:
      clean_user = username.strip().upper()
      if (
          clean_user in VALID_STAFF_DIRECTORY
          and password == VALID_STAFF_DIRECTORY[clean_user]["pin"]
      ):
        st.session_state["authenticated"] = True
        st.session_state["user_name"] = VALID_STAFF_DIRECTORY[clean_user][
            "name"
        ]
        st.session_state["user_role"] = VALID_STAFF_DIRECTORY[clean_user][
            "role"
        ]
        st.session_state["user_subcounty"] = VALID_STAFF_DIRECTORY[clean_user][
            "subcounty"
        ]
        st.success(
            f"Access Granted. Welcome back, {st.session_state['user_name']}!"
        )
        st.rerun()
      else:
        st.error(
            "⚠️ Authentication Failed: Invalid Staff ID or secure PIN. Please"
            " use the official demo credentials provided above."
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
  phones = [
      f"07{np.random.choice([1, 2, 9])}{np.random.randint(1000000, 9999999)}"
      for _ in range(n_rows)
  ]
  sub_counties = np.random.choice(
      [
          "Karatina / Mathira East",
          "Othaya Town",
          "Mukurwe-ini Centre",
          "Nyeri Central / Town",
          "Tetu Sub-County",
      ],
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
      ["Passed", "Rejected", "Conditional Pass"],
      size=n_rows,
      p=[0.72, 0.20, 0.08],
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
      "Phone_Number": phones,
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

if "schedules" not in st.session_state:
  st.session_state["schedules"] = pd.DataFrame({
      "Sub_County": [
          "Karatina / Mathira East",
          "Othaya Town",
          "Nyeri Central / Town",
      ],
      "Verification_Center": [
          "Karatina Open Market Hall",
          "Othaya Social Hall",
          "Nyeri Town Sub-County Office",
      ],
      "Start_Date": ["2026-11-01", "2026-11-15", "2026-12-01"],
      "End_Date": ["2026-11-05", "2026-11-18", "2026-12-05"],
      "Assigned_Inspector": [
          "Insp. Mwangi (ID: 042)",
          "Insp. Ndirangu (ID: 018)",
          "Insp. Wanjiku (ID: 025)",
      ],
      "Status": ["Scheduled", "Scheduled", "Upcoming"],
  })


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
st.sidebar.markdown(f"👤 **User:** {st.session_state['user_name']}")
st.sidebar.markdown(f"🛡️ **Role:** {st.session_state['user_role']}")
st.sidebar.markdown(f"📍 **Station:** {st.session_state['user_subcounty']}")
st.sidebar.markdown("---")

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
    "*Replacing manual paper logbooks with automated fraud prevention, real-time"
    " analytics, circuit scheduling, and cashless revenue management.*"
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Revenue & Compliance Trends",
    "📂 Digital Archive (Search & Export)",
    "📝 Field Inspection Portal (M-Pesa Verified)",
    "📅 Circuit Schedules & SMS Notices",
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
      "Search Trader Name, Phone Number, or M-Pesa Code:",
      placeholder="Type trader name, 07xx phone, or M-Pesa code...",
  )

  display_df = filtered_df
  if search_query:
    display_df = display_df[
        display_df["Trader_Name"].str.contains(
            search_query, case=False, na=False
        )
        | display_df["Phone_Number"].str.contains(
            search_query, case=False, na=False
        )
        | display_df["Mpesa_Code"].str.contains(
            search_query, case=False, na=False
        )
    ]

  st.dataframe(display_df, use_container_width=True)
  st.caption(
      f"Displaying {len(display_df)} official records (with contact details"
      " for SMS broadcasts)."
  )

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
          "Trader Phone Number (M-Pesa / SMS Alerts)", placeholder="0712345678"
      )
    with f_col2:
      new_subcounty = st.selectbox(
          "Sub-County",
          [
              "Karatina / Mathira East",
              "Othaya Town",
              "Mukurwe-ini Centre",
              "Nyeri Central / Town",
              "Tetu Sub-County",
          ],
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

    submitted = st.form_submit_button("Verify Payment & Issue Certificate")

    if submitted:
      clean_code = mpesa_code.strip().upper()
      clean_phone = (
          phone_number.strip() if phone_number.strip() != "" else "0700000000"
      )

      if new_trader.strip() == "":
        st.warning("Please enter a valid Trader / Business Name.")
      elif len(clean_code) < 8:
        st.error(
            "⚠️ Transaction Blocked: Valid M-Pesa confirmation code required"
            " (Cash payments are strictly prohibited)."
        )
      elif clean_code in st.session_state["df"]["Mpesa_Code"].values:
        st.error(
            f"🚨 FRAUD ALERT: M-Pesa code **{clean_code}** has already been"
            " processed! Code reuse is strictly locked."
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
            "Phone_Number": [clean_phone],
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
            "phone": clean_phone,
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
            f" **{clean_code}**! Digital entry logged."
        )

  if st.session_state["last_receipt_data"] is not None:
    r = st.session_state["last_receipt_data"]
    st.markdown("---")
    st.subheader("🧾 Verification Certificate Preview")

    receipt_html = f"""
        <style>
        .receipt-box {{
            border: 2px dashed #006837;
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
                <p style="margin:0; font-size:16px; color:#006837;"><b>COUNTY GOVERNMENT OF NYERI</b></p>
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

    pdf_bytes = generate_pdf_receipt(r)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Official Receipt (PDF)",
        data=pdf_bytes,
        file_name=f"Certificate_{r['trader']}_{r['code']}.pdf",
        mime="application/pdf",
    )

with tab4:
  st.subheader(
      "📅 Public Inspection Schedules & Mass SMS Broadcast Engine"
  )
  st.markdown(
      "Publish upcoming inspection centers, schedule field circuits per"
      " sub-county, and dispatch high-volume SMS notifications directly to"
      " registered trader mobile numbers."
  )

  col_sched1, col_sched2 = st.columns([1, 1])

  with col_sched1:
    st.markdown("### 📌 Published County Stamping Circuits")
    st.dataframe(st.session_state["schedules"], use_container_width=True)

    with st.expander("➕ Schedule New Stamping Circuit"):
      with st.form("new_schedule_form"):
        sc_subcounty = st.selectbox(
            "Target Sub-County",
            [
                "Karatina / Mathira East",
                "Othaya Town",
                "Mukurwe-ini Centre",
                "Nyeri Central / Town",
                "Tetu Sub-County",
            ],
        )
        sc_center = st.text_input(
            "Inspection Center / Venue", placeholder="e.g., Karatina Social Hall"
        )
        sc_col_dates1, sc_col_dates2 = st.columns(2)
        with sc_col_dates1:
          sc_start = st.date_input("Start Date", value=datetime.today())
        with sc_col_dates2:
          sc_end = st.date_input(
              "End Date", value=datetime.today() + timedelta(days=5)
          )
        sc_inspector = st.text_input(
            "Assigned Lead Inspector", placeholder="e.g., Insp. Kiptoo (ID: 031)"
        )

        sc_submit = st.form_submit_button("Publish Circuit Schedule")

        if sc_submit:
          if sc_center.strip() == "":
            st.warning("Please enter a valid venue or inspection center.")
          else:
            new_sched = pd.DataFrame({
                "Sub_County": [sc_subcounty],
                "Verification_Center": [sc_center],
                "Start_Date": [sc_start.strftime("%Y-%m-%d")],
                "End_Date": [sc_end.strftime("%Y-%m-%d")],
                "Assigned_Inspector": [sc_inspector],
                "Status": ["Scheduled"],
            })
            st.session_state["schedules"] = pd.concat(
                [st.session_state["schedules"], new_sched], ignore_index=True
            )
            st.success(
                f"Circuit published for {sc_subcounty} at {sc_center}!"
            )
            st.rerun()

  with col_sched2:
    st.markdown("### 🚀 High-Volume Bulk SMS Engine")

    if len(st.session_state["schedules"]) > 0:
      selected_circuit_idx = st.selectbox(
          "Select Active Circuit for Mass Alert:",
          options=range(len(st.session_state["schedules"])),
          format_func=lambda i: (
              f"{st.session_state['schedules'].iloc[i]['Sub_County']} -"
              f" {st.session_state['schedules'].iloc[i]['Verification_Center']}"
          ),
      )

      c_row = st.session_state["schedules"].iloc[selected_circuit_idx]
      target_subcounty = c_row["Sub_County"]

      # Filter registered traders in target sub-county with phone numbers
      matched_traders_df = st.session_state["df"][
          st.session_state["df"]["Sub_County"] == target_subcounty
      ]
      trader_count = len(matched_traders_df)

      # SMS Metrics Display
      m_col1, m_col2, m_col3 = st.columns(3)
      m_col1.metric("Target Contacts", f"{trader_count:,}")
      m_col2.metric("Estimated SMS Units", f"{trader_count:,}")
      m_col3.metric("Est. Cost @ KES 0.60", f"KES {trader_count * 0.60:,.2f}")

      st.markdown("---")

      sms_template = (
          f"COUNTY GOV OF NYERI NOTICE: Weights & Measures annual verification"
          f" for {target_subcounty} will take place at {c_row['Verification_Center']}"
          f" from {c_row['Start_Date']} to {c_row['End_Date']}. All trade weighing"
          f" equipment must be presented. Payment via M-Pesa only. Mandatory compliance."
      )

      st.text_area(
          "Generated SMS Broadcast Content:", value=sms_template, height=120
      )

      # Broadcast Execution Simulation
      if st.button("📲 Execute Mass Broadcast via Bulk Gateway"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Simulate batching progress
        batch_size = max(1, trader_count // 10)
        for i in range(1, 11):
          time.sleep(0.15)  # Simulate API latency
          percent = i * 10
          progress_bar.progress(percent)
          sent_so_far = min(i * batch_size, trader_count)
          status_text.text(
              f"⚡ Dispatching SMS Batch {i}/10... ({sent_so_far:,} /"
              f" {trader_count:,} delivered)"
          )

        status_text.empty()
        progress_bar.empty()

        st.success(
            f"✅ **MASS BROADCAST COMPLETE:** Successfully delivered"
            f" **{trader_count:,} SMS alerts** to registered traders in"
            f" **{target_subcounty}** via standard Telecom Bulk API!"
        )

        # Show Sample Recipient Queue
        with st.expander("📄 View Sample Recipient Dispatch Logs"):
          sample_dispatch = matched_traders_df[
              ["Trader_Name", "Phone_Number", "Sub_County"]
          ].head(10).copy()
          sample_dispatch["Delivery_Status"] = "DELIVERED (HTTP 200 OK)"
          sample_dispatch["Timestamp"] = datetime.now().strftime(
              "%Y-%m-%d %H:%M:%S"
          )
          st.dataframe(sample_dispatch, use_container_width=True)
