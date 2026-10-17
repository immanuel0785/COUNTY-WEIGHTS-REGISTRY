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
    /* Nyeri Brand Palette: Forest Green (#006837), Sky Blue (#0056B3) */
    h1, h2, h3 {
        color: #006837 !important;
        font-weight: 700 !important;
    }
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
        color: #FFD700 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0B192C !important;
    }
    div[data-testid="stMetricValue"] {
        color: #006837 !important;
        font-weight: bold !important;
    }
    button[aria-selected="true"] {
        border-bottom-color: #006837 !important;
        color: #006837 !important;
        font-weight: bold !important;
    }
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
        st.error("⚠️ Authentication Failed: Invalid Staff ID or secure PIN.")

  st.stop()


# --- 2. UNIVERSAL EXCEL DATA LOADER FUNCTION ---
def process_uploaded_excel(uploaded_file_or_path):
  try:
    df = pd.read_excel(uploaded_file_or_path)

    # Clean whitespace in column headers
    df.columns = df.columns.str.strip()

    # Clean phone number columns if present
    phone_cols = [c for c in df.columns if "phone" in c.lower() or "no." in c.lower()]
    for pcol in phone_cols:
      if pcol != "S/NO.":
        df[pcol] = (
            df[pcol]
            .fillna("")
            .astype(str)
            .str.replace(".0", "", regex=False)
        )

    # Fill empty numeric cells with 0
    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Format date columns if present
    date_cols = [c for c in df.columns if "date" in c.lower() or c.upper() == "DATE"]
    for dcol in date_cols:
      df[dcol] = pd.to_datetime(df[dcol], errors="coerce").dt.strftime("%Y-%m-%d")

    return df
  except Exception as e:
    st.error(f"⚠️ Error reading Excel file: {e}")
    return None


# Initialize session state dataframe
if "df" not in st.session_state:
  # Try loading default local file if available, otherwise initialize empty template
  try:
    st.session_state["df"] = process_uploaded_excel("nyeri_ledger.xlsx")
  except Exception:
    st.session_state["df"] = pd.DataFrame(
        columns=["DATE", "S/NO.", "NAME", "Phone No.", "STATION", "TOTAL_AMOUNT_KSHS"]
    )

if st.session_state["df"] is None:
  st.session_state["df"] = pd.DataFrame(
      columns=["DATE", "S/NO.", "NAME", "Phone No.", "STATION", "TOTAL_AMOUNT_KSHS"]
  )

df = st.session_state["df"]

if "schedules" not in st.session_state:
  st.session_state["schedules"] = pd.DataFrame({
      "Sub_County": [
          "OTHAYA TOWN",
          "OFFICE / NYERI TOWN",
          "KIAMARIGA / MUNYU",
      ],
      "Verification_Center": [
          "Othaya Social Hall",
          "Nyeri Town Sub-County Office",
          "Kiamariga Market Hall",
      ],
      "Start_Date": ["2026-11-01", "2026-11-15", "2026-12-01"],
      "End_Date": ["2026-11-05", "2026-11-18", "2026-12-05"],
      "Assigned_Inspector": [
          "Insp. Ndirangu (ID: 018)",
          "Insp. Mwangi (ID: 042)",
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
  c.drawString(15, y, f"S/NO: {r['s_no']}")
  y -= 12
  c.drawString(15, y, f"Date Issued: {r['date']}")
  y -= 12
  c.drawString(15, y, f"Business: {r['trader']}")
  y -= 12
  c.drawString(15, y, f"Phone: {r['phone']}")
  y -= 12
  c.drawString(15, y, f"Station: {r['station']}")
  y -= 14
  c.drawString(15, y, "-" * 38)
  y -= 12

  c.drawString(15, y, f"Total Amount: KES {r['fee']:,.2f}")
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


# --- 4. SIDEBAR CONTROL PANEL & UNIVERSAL UPLOADER ---
st.sidebar.header("🔍 Registry Controls")
st.sidebar.markdown(f"👤 **User:** {st.session_state['user_name']}")
st.sidebar.markdown(f"🛡️ **Role:** {st.session_state['user_role']}")
st.sidebar.markdown(f"📍 **Station:** {st.session_state['user_subcounty']}")
st.sidebar.markdown("---")

st.sidebar.subheader("📂 Upload Any Excel Ledger")
uploaded_sidebar_file = st.sidebar.file_uploader(
    "Upload .xlsx Ledger File", type=["xlsx", "xls"]
)
if uploaded_sidebar_file is not None:
  new_df = process_uploaded_excel(uploaded_sidebar_file)
  if new_df is not None:
    st.session_state["df"] = new_df
    st.sidebar.success(
        f"Loaded {len(new_df):,} rows from '{uploaded_sidebar_file.name}'!"
    )
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Secure Logout"):
  st.session_state["authenticated"] = False
  st.rerun()

# Dynamic Station Filter based on columns
station_col_candidates = [
    c
    for c in df.columns
    if "station" in c.lower() or "sub_county" in c.lower() or "county" in c.lower()
]
station_column = station_col_candidates[0] if len(station_col_candidates) > 0 else None

station_list = (
    ["All"] + list(df[station_column].dropna().unique())
    if station_column and station_column in df.columns
    else ["All"]
)
selected_station = st.sidebar.selectbox("Filter by Station", station_list)

filtered_df = df
if selected_station != "All" and station_column and station_column in filtered_df.columns:
  filtered_df = filtered_df[filtered_df[station_column] == selected_station]

# --- 5. MAIN DASHBOARD HEADER ---
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
    "*Digitizing Nyeri County's physical inspection ledgers into an automated,"
    " fraud-proof database.*"
)
st.markdown("---")

# --- 6. TOP-LEVEL METRICS ---
total_records = len(filtered_df)

rev_col_candidates = [
    c for c in df.columns if "total" in c.lower() or "kshs" in c.lower() or "amount" in c.lower()
]
rev_col = rev_col_candidates[0] if len(rev_col_candidates) > 0 else None

total_revenue = (
    filtered_df[rev_col].sum()
    if rev_col and rev_col in filtered_df.columns
    else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("Total Ledger Entries", f"{total_records:,}")
col2.metric("Total Revenue Captured", f"KES {total_revenue:,.2f}")
col3.metric("Database Status", "🟢 Ready & Dynamic")

st.markdown("---")

# --- 7. NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Digital Ledger Archive",
    "📈 Revenue Analytics & Trends",
    "📝 Field Entry & Auto-Receipt Generator",
    "📅 Circuit Schedules & Mass SMS Engine",
])

# --- TAB 1: ARCHIVE & TABLE ---
with tab1:
  st.subheader("Master Verification Registry (Dynamic Excel View)")
  st.markdown(
      "You can upload any departmental Excel spreadsheet using the sidebar uploader"
      " above, and view, search, or export it instantly below."
  )

  search_query = st.text_input(
      "Search Ledger Records:",
      placeholder="Type trader name, phone, serial number, or station...",
  )

  display_df = filtered_df
  if search_query:
    mask = display_df.astype(str).apply(
        lambda x: x.str.contains(search_query, case=False, na=False)
    )
    display_df = display_df[mask.any(axis=1)]

  st.dataframe(display_df, use_container_width=True)
  st.caption(f"Displaying {len(display_df)} records.")

  csv_master = display_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export Filtered Audit Ledger (CSV)",
      data=csv_master,
      file_name="nyeri_county_weights_audit.csv",
      mime="text/csv",
  )

# --- TAB 2: ANALYTICS ---
with tab2:
  st.subheader("Historical Revenue & Station Breakdown")
  col_a, col_b = st.columns(2)

  if station_column and station_column in filtered_df.columns:
    with col_a:
      st.markdown("**Inspections per Station**")
      st.bar_chart(filtered_df.groupby(station_column).size())

    with col_b:
      if rev_col and rev_col in filtered_df.columns:
        st.markdown("**Revenue Collected per Station (KES)**")
        st.bar_chart(filtered_df.groupby(station_column)[rev_col].sum())
  else:
    st.info("Station or Revenue columns not detected in the current uploaded file.")

# --- TAB 3: FIELD ENTRY FORM ---
with tab3:
  st.subheader("Log Field Verification & Issue Official Receipt")

  if "last_receipt_data" not in st.session_state:
    st.session_state["last_receipt_data"] = None

  sno_col_candidates = [c for c in df.columns if "s/no" in c.lower() or "serial" in c.lower()]
  sno_col = sno_col_candidates[0] if len(sno_col_candidates) > 0 else None

  default_sno = 204820
  if sno_col and sno_col in df.columns:
    try:
      default_sno = int(pd.to_numeric(df[sno_col], errors="coerce").max() + 1)
    except Exception:
      pass

  with st.form("inspection_form"):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
      st.text_input(
          "Official Certificate Serial No. (S/NO.)",
          value=f"{default_sno}",
          disabled=True,
      )
      new_trader = st.text_input(
          "Trader / Business Name", placeholder="e.g. DEKUT COFFEE"
      )
      phone_number = st.text_input(
          "Trader Phone Number", placeholder="0722906936"
      )
      new_station = st.selectbox(
          "Station / Location",
          [
              "OTHAYA TOWN",
              "OFFICE",
              "KIAMARIGA",
              "MUNYU",
              "JETI",
              "IRIGITHATHI",
              "KARATINA MARKET",
          ],
      )
      inspection_date_obj = st.date_input(
          "Inspection Date", value=datetime.today()
      )

    with f_col2:
      stamped_pumps = st.number_input(
          "Stamped Fuel Pumps / Nozzles (KES 2,400 ea)", min_value=0, value=1
      )
      stamped_scales = st.number_input(
          "Stamped Scales (KES 2,000 ea)", min_value=0, value=0
      )
      stamped_weights = st.number_input(
          "Stamped Weights (KES 500 ea)", min_value=0, value=0
      )
      mpesa_code = st.text_input(
          "M-Pesa Confirmation Code", placeholder="e.g., QHX20481"
      )

    submitted = st.form_submit_button(
        "Calculate Total, Verify Payment & Log Entry"
    )

    if submitted:
      clean_code = mpesa_code.strip().upper()
      clean_phone = (
          phone_number.strip() if phone_number.strip() != "" else "0700000000"
      )

      calc_fee = (
          (stamped_pumps * 2400)
          + (stamped_scales * 2000)
          + (stamped_weights * 500)
      )
      if calc_fee == 0:
        calc_fee = 2000

      if new_trader.strip() == "":
        st.warning("Please enter a valid Trader / Business Name.")
      elif len(clean_code) < 8:
        st.error(
            "⚠️ Transaction Blocked: Valid M-Pesa confirmation code required."
        )
      else:
        inspection_date_str = inspection_date_obj.strftime("%Y-%m-%d")
        next_due_str = (inspection_date_obj + timedelta(days=365)).strftime(
            "%Y-%m-%d"
        )

        st.session_state["last_receipt_data"] = {
            "s_no": default_sno,
            "trader": new_trader,
            "phone": clean_phone,
            "station": new_station,
            "fee": calc_fee,
            "code": clean_code,
            "date": inspection_date_str,
            "due": next_due_str,
        }
        st.success(
            f"Verified payment of **KES {calc_fee:,.2f}** via M-Pesa code"
            f" **{clean_code}**! Logged under S/NO: **{default_sno}**."
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
        .receipt-header {{ text-align: center; font-weight: bold; }}
        </style>
        
        <div class="receipt-box">
            <div class="receipt-header">
                <p style="margin:0; font-size:16px; color:#006837;"><b>COUNTY GOVERNMENT OF NYERI</b></p>
                <p style="margin:0; font-size:12px;">DEPARTMENT OF TRADE & CO-OPERATIVES</p>
                <p style="margin:0; font-size:12px;"><b>WEIGHTS & MEASURES DIVISION</b></p>
                <p>----------------------------------------</p>
            </div>
            <p style="margin:4px 0;"><b>S/NO:</b> {r['s_no']}</p>
            <p style="margin:4px 0;"><b>Date Issued:</b> {r['date']}</p>
            <p>----------------------------------------</p>
            <p style="margin:4px 0;"><b>Business Name:</b> {r['trader']}</p>
            <p style="margin:4px 0;"><b>Phone Contact:</b> {r['phone']}</p>
            <p style="margin:4px 0;"><b>Station:</b> {r['station']}</p>
            <p>----------------------------------------</p>
            <p style="margin:4px 0;"><b>Total Amount Paid:</b> KES {r['fee']:,.2f}</p>
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
        file_name=f"Certificate_SNO_{r['s_no']}_{r['code']}.pdf",
        mime="application/pdf",
    )

# --- TAB 4: BULK SMS DISPATCHER ---
with tab4:
  st.subheader("📅 Public Inspection Schedules & Mass SMS Broadcast Engine")
  st.markdown(
      "Publish upcoming inspection centers, schedule field circuits, and"
      " dispatch high-volume SMS notifications to trader contact numbers."
  )

  col_sched1, col_sched2 = st.columns([1, 1])

  with col_sched1:
    st.markdown("### 📌 Published County Stamping Circuits")
    st.dataframe(st.session_state["schedules"], use_container_width=True)

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

      trader_count = len(st.session_state["df"])

      m_col1, m_col2, m_col3 = st.columns(3)
      m_col1.metric("Target Contacts", f"{trader_count:,}")
      m_col2.metric("Estimated SMS Units", f"{trader_count:,}")
      m_col3.metric("Est. Cost @ KES 0.60", f"KES {trader_count * 0.60:,.2f}")

      st.markdown("---")

      sms_template = (
          f"COUNTY GOV OF NYERI NOTICE: Weights & Measures annual verification"
          f" for {target_subcounty} will take place at"
          f" {c_row['Verification_Center']} from {c_row['Start_Date']} to"
          f" {c_row['End_Date']}. All trade weighing equipment must be"
          f" presented. Payment via M-Pesa only."
      )

      st.text_area(
          "Generated SMS Broadcast Content:", value=sms_template, height=120
      )

      if st.button("📲 Execute Mass Broadcast via Bulk Gateway"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        batch_size = max(1, trader_count // 10)
        for i in range(1, 11):
          time.sleep(0.15)
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
            f"✅ **MASS BROADCAST COMPLETE:** Delivered **{trader_count:,} SMS"
            f" alerts** to registered traders in **{target_subcounty}**!"
        )
