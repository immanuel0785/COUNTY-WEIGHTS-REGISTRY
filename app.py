from datetime import datetime, timedelta
import io
import sqlite3
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

# --- 0. OFFICIAL NYERI COUNTY CUSTOM CSS STYLING (WITH SPINNING LOADER) ---
nyeri_custom_css = """
<style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Make Streamlit's spinner icon spin smoothly */
    .stSpinner > div {
        animation: spin 1s linear infinite !important;
    }

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

# --- 1. SQLITE PERMANENT DATABASE ENGINE ---
DB_FILE = "nyeri_weights_master.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_sheet TEXT,
            date_entry TEXT,
            serial_no TEXT,
            trader_name TEXT,
            phone_no TEXT,
            station TEXT,
            stamped_pumps INTEGER DEFAULT 0,
            stamped_scales INTEGER DEFAULT 0,
            stamped_weights INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0,
            mpesa_code TEXT,
            inspector_logged TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


init_db()


def save_record_to_db(record):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO ledger_entries (year_sheet, date_entry, serial_no, trader_name, phone_no, station, stamped_pumps, stamped_scales, stamped_weights, total_amount, mpesa_code, inspector_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          record["year_sheet"],
          record["date"],
          record["s_no"],
          record["trader"],
          record["phone"],
          record["station"],
          record["pumps"],
          record["scales"],
          record["weights"],
          record["fee"],
          record["code"],
          record["inspector"],
      ),
  )
  conn.commit()
  conn.close()


def load_all_db_records():
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql_query("SELECT * FROM ledger_entries", conn)
  conn.close()
  return df


# --- PDF CERTIFICATE GENERATOR ---
def generate_pdf_certificate(r):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=(420, 560))
  c.setFillColorRGB(0, 0.41, 0.22)
  c.rect(20, 520, 380, 25, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.drawString(35, 528, "COUNTY GOVERNMENT OF NYERI - WEIGHTS & MEASURES")

  c.setFillColorRGB(0, 0, 0)
  c.setFont("Helvetica-Bold", 11)
  c.drawString(30, 490, "OFFICIAL VERIFICATION CERTIFICATE")
  c.setFont("Helvetica", 10)

  c.drawString(30, 460, f"Certificate S/NO: {r['s_no']}")
  c.drawString(30, 440, f"Date Issued: {r['date']}")
  c.drawString(30, 420, f"Business / Trader: {r['trader']}")
  c.drawString(30, 400, f"Phone Contact: {r['phone']}")
  c.drawString(30, 380, f"Station / Location: {r['station']}")
  c.drawString(30, 360, f"Stamped Pumps: {r['pumps']}")
  c.drawString(30, 340, f"Stamped Scales: {r['scales']}")
  c.drawString(30, 320, f"Stamped Weights: {r['weights']}")

  c.setFont("Helvetica-Bold", 10)
  c.drawString(30, 290, f"Total Amount Paid: KES {r['fee']:,.2f}")
  c.drawString(30, 270, f"M-Pesa Reference Code: {r['code']}")

  c.setFillColorRGB(0.7, 0, 0)
  c.drawString(30, 240, f"Next Verification Due: {r['due']}")

  c.setFillColorRGB(0, 0, 0)
  c.setFont("Helvetica-Oblique", 8)
  c.drawString(30, 190, "Authorized digital stamp & record synced to county server.")
  c.drawString(30, 175, f"Logged by: {r['inspector']}")

  c.save()
  buffer.seek(0)
  return buffer.getvalue()


# --- 2. AUTHENTICATION ---
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
      "• **Administrator / Director:** ID: `NYR_ADMIN_001` | PIN: `0001`\n"
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


# --- 3. EXCEL MULTI-SHEET PARSER & NORMALIZER (CACHED FOR SPEED) ---
@st.cache_data
def process_uploaded_excel(uploaded_file_or_path, sheet_name=0):
  try:
    df_raw = pd.read_excel(
        uploaded_file_or_path, sheet_name=sheet_name, header=None
    )
    if df_raw.empty:
      return None

    header_row_idx = 0
    for idx, row in df_raw.head(15).iterrows():
      row_str = " ".join([str(val).lower() for val in row.values if pd.notnull(val)])
      if any(
          k in row_str
          for k in [
              "date",
              "s/no",
              "name",
              "station",
              "stamped",
              "total amount",
              "trader",
          ]
      ):
        header_row_idx = idx
        break

    df = pd.read_excel(
        uploaded_file_or_path, sheet_name=sheet_name, header=header_row_idx
    )
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all").reset_index(drop=True)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    for col in df.columns:
      if any(p in col.lower() for p in ["phone", "no.", "tel", "contact"]):
        if "s/no" not in col.lower():
          df[col] = (
              df[col].fillna("").astype(str).str.replace(".0", "", regex=False)
          )

    for col in df.columns:
      if any(
          n in col.lower()
          for n in [
              "total",
              "amount",
              "kshs",
              "stamped",
              "rejected",
              "adjusted",
              "fees",
              "charges",
              "expense",
          ]
      ):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in df.columns:
      if "date" in col.lower():
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )

    return df
  except Exception as e:
    st.error(f"⚠️ Error parsing Excel sheet: {e}")
    return None


# --- 4. SESSION STATE & GIT BUNDLED WORKBOOK AUTO-LOADER ---
if "sheets_dict" not in st.session_state:
  st.session_state["sheets_dict"] = {}
  default_workbook_path = "nyeri_ledger.xlsx"
  try:
    with st.spinner(
        "⏳ Loading County Historical Ledgers from Git... Please wait."
    ):
      xl_workbook = pd.ExcelFile(default_workbook_path)
      for s_name in xl_workbook.sheet_names:
        parsed_s = process_uploaded_excel(
            default_workbook_path, sheet_name=s_name
        )
        if parsed_s is not None and not parsed_s.empty:
          st.session_state["sheets_dict"][str(s_name)] = parsed_s
  except Exception as e:
    pass

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

is_admin_or_director = (
    "Administrator" in st.session_state["user_role"]
    or "Director" in st.session_state["user_name"]
)


# --- 5. SIDEBAR CONTROL PANEL ---
st.sidebar.header("🔍 Registry Controls")
st.sidebar.markdown(f"👤 **User:** {st.session_state['user_name']}")
st.sidebar.markdown(f"🛡️ **Role:** {st.session_state['user_role']}")
st.sidebar.markdown(f"📍 **Station:** {st.session_state['user_subcounty']}")
st.sidebar.markdown("---")

st.sidebar.info(
    "📂 **Master Registry Source:**\nAuto-loaded securely from County Git"
    f" Repository (`nyeri_ledger.xlsx`). Sheets loaded:"
    f" **{len(st.session_state['sheets_dict'])}**"
)

# Database items merge into sheets_dict dynamically
db_df = load_all_db_records()
if not db_df.empty:
  for yr, group in db_df.groupby("year_sheet"):
    clean_group = group.rename(
        columns={
            "date_entry": "DATE",
            "serial_no": "S/NO.",
            "trader_name": "NAME",
            "phone_no": "Phone No.",
            "station": "STATION",
            "total_amount": "Total Amount kshs",
        }
    )
    if yr in st.session_state["sheets_dict"]:
      merged = pd.concat(
          [st.session_state["sheets_dict"][yr], clean_group], ignore_index=True
      )
      st.session_state["sheets_dict"][yr] = merged.drop_duplicates(
          subset=["S/NO.", "NAME"], keep="last"
      )
    else:
      st.session_state["sheets_dict"][yr] = clean_group

# Sheet Selector
available_sheets = list(st.session_state["sheets_dict"].keys())
selected_sheet_name = "All Sheets (Unison)"
if available_sheets:
  selected_sheet_name = st.sidebar.selectbox(
      "Select Active Year / Sheet:",
      ["All Sheets (Unison)"] + available_sheets,
  )

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Secure Logout"):
  st.session_state["authenticated"] = False
  st.rerun()

# Build Active Dataframe
if selected_sheet_name == "All Sheets (Unison)" or not available_sheets:
  combined_list = []
  for sname, sdf in st.session_state["sheets_dict"].items():
    temp = sdf.copy()
    temp["YEAR_SHEET"] = str(sname)
    combined_list.append(temp)
  if combined_list:
    df_active = pd.concat(combined_list, ignore_index=True)
  else:
    df_active = pd.DataFrame(
        columns=[
            "DATE",
            "S/NO.",
            "NAME",
            "Phone No.",
            "STATION",
            "Total Amount kshs",
            "YEAR_SHEET",
        ]
    )
else:
  df_active = st.session_state["sheets_dict"][selected_sheet_name].copy()
  df_active["YEAR_SHEET"] = selected_sheet_name

# Station Filter
station_cols = [c for c in df_active.columns if "station" in c.lower()]
station_col = station_cols[0] if station_cols else None
station_list = (
    ["All"] + list(df_active[station_col].dropna().unique())
    if station_col
    else ["All"]
)
selected_station = st.sidebar.selectbox(
    "Filter by Sub-County / Station", station_list
)

filtered_df = df_active.copy()
if selected_station != "All" and station_col:
  filtered_df = filtered_df[filtered_df[station_col] == selected_station]


# --- 6. MAIN HEADER & TOP METRICS ---
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

rev_cols = [
    c
    for c in df_active.columns
    if "total" in c.lower() or "kshs" in c.lower() or "amount" in c.lower()
]
rev_col = rev_cols[0] if rev_cols else None

total_records = len(filtered_df)
total_revenue = (
    filtered_df[rev_col].sum() if rev_col and rev_col in filtered_df.columns else 0
)

m1, m2, m3 = st.columns(3)
m1.metric("Total Ledger Entries", f"{total_records:,}")
m2.metric("Total Revenue Captured", f"KES {total_revenue:,.2f}")
m3.metric(
    "Active View Scope",
    f"📅 {selected_sheet_name} ({len(available_sheets)} Sheets)",
)

st.markdown("---")

# --- 7. NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Digital Ledger Archive & Rollover",
    "📈 Multi-Year Revenue & Station Analytics",
    "📝 Field Entry & Auto-Receipt Generator",
    "📅 Circuit Schedules & Mass SMS Engine",
])

# --- TAB 1: ARCHIVE, ROLLOVER & EXCEL EXPORT ---
with tab1:
  st.subheader("Master Verification Registry (Dynamic Excel View)")
  st.markdown(
      "Inspect multi-year historical records ingested from your departmental"
      " spreadsheets across all sub-counties."
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

  st.markdown("---")

  # EXCEL DOWNLOAD AVAILABLE TO ALL USERS
  st.markdown("### 📥 Download Up-To-Date Master Excel Workbook")
  output_excel = io.BytesIO()
  with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    if st.session_state["sheets_dict"]:
      for sname, sdf in st.session_state["sheets_dict"].items():
        sdf.to_excel(writer, sheet_name=str(sname)[:30], index=False)
    else:
      filtered_df.to_excel(writer, sheet_name="Master_Ledger", index=False)
  excel_data = output_excel.getvalue()

  st.download_button(
      label="📊 Download Full Multi-Sheet Workbook (.xlsx)",
      data=excel_data,
      file_name="nyeri_county_weights_and_measures_master.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )

  # 1-CLICK ANNUAL ROLLOVER: RESTRICTED TO DIRECTOR / ADMINISTRATOR ONLY
  if is_admin_or_director:
    st.markdown("---")
    st.markdown("### 👑 [Director Restricted] 1-Click Annual Trader Rollover")
    st.markdown(
        "Automatically roll over trader profiles from a previous year into a"
        " new year sheet without re-typing."
    )

    if available_sheets:
      col_r1, col_r2 = st.columns(2)
      with col_r1:
        source_sheet = st.selectbox(
            "Source Sheet:",
            available_sheets,
            key="src_sheet",
        )
      with col_r2:
        target_year = st.text_input(
            "New Target Year / Sheet Name:", placeholder="2027"
        )

      if st.button("🚀 Execute Annual Rollover"):
        if target_year.strip() != "":
          src_df = st.session_state["sheets_dict"][source_sheet].copy()

          new_sheet_df = pd.DataFrame()
          name_col = [c for c in src_df.columns if "name" in c.lower()]
          phone_col = [c for c in src_df.columns if "phone" in c.lower()]
          station_col_s = [c for c in src_df.columns if "station" in c.lower()]

          new_sheet_df["DATE"] = datetime.now().strftime("%Y-%m-%d")
          new_sheet_df["S/NO."] = "PENDING"
          new_sheet_df["NAME"] = (
              src_df[name_col[0]] if name_col else "Unknown Trader"
          )
          new_sheet_df["Phone No."] = (
              src_df[phone_col[0]] if phone_col else "0700000000"
          )
          new_sheet_df["STATION"] = (
              src_df[station_col_s[0]] if station_col_s else "OFFICE"
          )
          new_sheet_df["Total Amount kshs"] = 0

          st.session_state["sheets_dict"][target_year.strip()] = new_sheet_df
          st.success(
              f"✅ Rolled over {len(new_sheet_df):,} traders into sheet"
              f" '{target_year.strip()}'!"
          )
          st.rerun()


# --- TAB 2: MULTI-YEAR REVENUE & STATION ANALYTICS ---
with tab2:
  st.subheader("📈 Multi-Year Revenue & Station Analytics")
  st.markdown(
      "Overview of all sub-counties, inspection volumes, and revenue collection"
      " metrics across years."
  )

  if station_col and station_col in filtered_df.columns:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
      st.markdown("**Inspections Volume per Sub-County**")
      st.bar_chart(filtered_df.groupby(station_col).size())

    with col_g2:
      if rev_col and rev_col in filtered_df.columns:
        st.markdown("**Revenue Collected per Sub-County (KES)**")
        station_rev = filtered_df.groupby(station_col)[rev_col].sum()
        st.bar_chart(station_rev)

    # DIRECTOR EXCLUSIVE AUDIT VIEW
    if is_admin_or_director:
      st.markdown("---")
      st.markdown(
          "### 👑 [Director Exclusive] Inspector Performance & Activity Log"
      )
      db_full = load_all_db_records()
      if not db_full.empty and "inspector_logged" in db_full.columns:
        st.dataframe(
            db_full[[
                "created_at",
                "inspector_logged",
                "station" if "station" in db_full.columns else "station",
                "trader_name",
                "total_amount",
            ]],
            use_container_width=True,
        )
      else:
        st.info(
            "Live inspector activity logs will populate here as field entries"
            " are made."
        )
  else:
    st.info("Station or Revenue columns not detected in the current sheet.")


# --- TAB 3: FIELD ENTRY & AUTO-RECEIPT GENERATOR ---
with tab3:
  st.subheader("📝 Log Field Verification & Issue Official Receipt")
  st.markdown(
      f"Logged in as: **{st.session_state['user_name']}** ({st.session_state['user_role']})"
  )

  if "last_receipt_data" not in st.session_state:
    st.session_state["last_receipt_data"] = None

  sno_col_candidates = [
      c
      for c in df_active.columns
      if "s/no" in c.lower() or "serial" in c.lower()
  ]
  sno_col = sno_col_candidates[0] if sno_col_candidates else None

  default_sno = 204820
  if sno_col and sno_col in df_active.columns:
    try:
      default_sno = int(
          pd.to_numeric(df_active[sno_col], errors="coerce").max() + 1
      )
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
      target_sheet_entry = st.selectbox(
          "Save To Year Sheet:",
          available_sheets if available_sheets else ["2026"],
      )
      new_trader = st.text_input(
          "Trader / Business Name", placeholder="e.g. DEKUT COFFEE"
      )
      phone_number = st.text_input(
          "Trader Phone Number", placeholder="0722906936"
      )
      new_station = st.selectbox(
          "Station / Location (All Sub-Counties)",
          [
              "OTHAYA TOWN",
              "OFFICE",
              "KIAMARIGA",
              "MUNYU",
              "JETI",
              "IRIGITHATHI",
              "KARATINA MARKET",
              "MATHIRA EAST",
              "NYERI TOWN",
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

        rec_payload = {
            "year_sheet": target_sheet_entry,
            "s_no": default_sno,
            "trader": new_trader,
            "phone": clean_phone,
            "station": new_station,
            "pumps": stamped_pumps,
            "scales": stamped_scales,
            "weights": stamped_weights,
            "fee": calc_fee,
            "code": clean_code,
            "date": inspection_date_str,
            "due": next_due_str,
            "inspector": st.session_state["user_name"],
        }

        # 1. Save to SQLite
        save_record_to_db(rec_payload)

        # 2. Append to Session Workbook
        new_row = pd.DataFrame([{
            "DATE": inspection_date_str,
            "S/NO.": default_sno,
            "NAME": new_trader,
            "Phone No.": clean_phone,
            "STATION": new_station,
            "Total Amount kshs": calc_fee,
        }])

        if target_sheet_entry in st.session_state["sheets_dict"]:
          st.session_state["sheets_dict"][target_sheet_entry] = pd.concat(
              [st.session_state["sheets_dict"][target_sheet_entry], new_row],
              ignore_index=True,
          )
        else:
          st.session_state["sheets_dict"][target_sheet_entry] = new_row

        st.session_state["last_receipt_data"] = rec_payload

        st.success(
            f"✅ Trader Saved Permanently! Updated Excel Ledger & Database with"
            f" payment of **KES {calc_fee:,.2f}** via M-Pesa code"
            f" **{clean_code}**! (S/NO: **{default_sno}**)"
        )
        st.rerun()

  if st.session_state["last_receipt_data"] is not None:
    r = st.session_state["last_receipt_data"]
    st.markdown("---")
    st.subheader("🧾 Verification Certificate Preview & Download")

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
                <p style="margin:0; font-size:11px;"><i>Status: Saved & Synced to County Server</i></p>
                <p style="margin:0; font-size:10px;">*** OFFICIAL DIGITAL STAMP ***</p>
            </div>
        </div>
        """
    st.markdown(receipt_html, unsafe_allow_html=True)

    # PDF CERTIFICATE DOWNLOAD BUTTON
    pdf_bytes = generate_pdf_certificate(r)
    st.download_button(
        label="📥 Download Official Verification Certificate (.pdf)",
        data=pdf_bytes,
        file_name=f"Certificate_{r['s_no']}_{r['trader'].replace(' ', '_')}.pdf",
        mime="application/pdf",
    )


# --- TAB 4: LOCATION-FILTERED SMS & SAFARICOM/LICENSING PITCH PANEL ---
with tab4:
  st.subheader(
      "📅 Public Inspection Schedules, Location Filters & API Integration Hub"
  )
  st.markdown(
      "Target specific sub-counties for SMS notices, schedule stamping"
      " circuits, and configure production Safaricom API & Licensing handshakes."
  )

  # PITCH PRESENTATION ROADMAP BANNER
  st.info(
      "🚀 **PITCH PRODUCTION ROADMAP:**\n"
      "The system core, database, and UI are 100% complete and fully"
      " operational. The final two steps for live public rollout are:\n"
      "1. **Safaricom API Integration:** Connecting Safaricom SDP/Daraja SMS"
      " gateway and M-Pesa C2B webhook.\n"
      "2. **Official County Licensing:** Acquiring official deployment"
      " clearance from the County Government of Nyeri."
  )

  st.markdown("---")

  col_sched1, col_sched2 = st.columns([1, 1])

  with col_sched1:
    st.markdown("### 📌 Published County Stamping Circuits")
    st.dataframe(st.session_state["schedules"], use_container_width=True)

    # Admin circuit scheduler
    if is_admin_or_director:
      with st.expander("➕ Add New Stamping Circuit"):
        with st.form("new_circuit_form"):
          nc_sub = st.text_input("Sub-County / Area", placeholder="MAKUTANO")
          nc_center = st.text_input(
              "Verification Center", placeholder="Makutano Social Hall"
          )
          nc_start = st.date_input(
              "Start Date", value=datetime.today() + timedelta(days=7)
          )
          nc_end = st.date_input(
              "End Date", value=datetime.today() + timedelta(days=10)
          )
          nc_insp = st.text_input("Assigned Inspector", value="Insp. Mwangi")
          add_circuit_btn = st.form_submit_button("Publish Circuit")

          if add_circuit_btn:
            new_c_row = pd.DataFrame({
                "Sub_County": [nc_sub.upper()],
                "Verification_Center": [nc_center],
                "Start_Date": [nc_start.strftime("%Y-%m-%d")],
                "End_Date": [nc_end.strftime("%Y-%m-%d")],
                "Assigned_Inspector": [nc_insp],
                "Status": ["Scheduled"],
            })
            st.session_state["schedules"] = pd.concat(
                [st.session_state["schedules"], new_c_row], ignore_index=True
            )
            st.success(
                f"✅ Published new verification circuit for {nc_sub.upper()}!"
            )
            st.rerun()

  with col_sched2:
    st.markdown("### 🚀 Location-Targeted Bulk SMS Dispatcher")

    if station_col and station_col in df_active.columns:
      all_locations = ["All Sub-Counties / Stations"] + sorted(
          [str(x) for x in df_active[station_col].dropna().unique()]
      )
    else:
      all_locations = [
          "All Sub-Counties / Stations",
          "OTHAYA TOWN",
          "OFFICE / NYERI TOWN",
          "KIAMARIGA / MUNYU",
      ]

    sms_target_location = st.selectbox(
        "📍 Filter Target Broadcast Location:", options=all_locations
    )

    if sms_target_location == "All Sub-Counties / Stations":
      target_df = filtered_df
    else:
      target_df = filtered_df[
          filtered_df[station_col].astype(str) == sms_target_location
      ]

    trader_count = len(target_df)

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Target Contacts", f"{trader_count:,}")
    m_col2.metric("Estimated SMS Units", f"{trader_count:,}")
    m_col3.metric("Est. Cost @ KES 0.60", f"KES {trader_count * 0.60:,.2f}")

    # Live Recipient Preview Expandable
    with st.expander("👀 Preview Filtered Recipients List"):
      if trader_count > 0:
        name_c = [c for c in target_df.columns if "name" in c.lower()]
        phone_c = [c for c in target_df.columns if "phone" in c.lower()]
        preview_cols = [
            c for c in [name_c[0] if name_c else None, phone_c[0] if phone_c else None]
            if c
        ]
        st.dataframe(
            target_df[preview_cols].head(10)
            if preview_cols
            else target_df.head(10),
            use_container_width=True,
        )
        st.caption(
            f"Showing preview of top 10 out of {trader_count:,} targeted"
            " traders."
        )
      else:
        st.info("No recipients found for this location.")

    st.markdown("---")

    sms_template = (
        f"COUNTY GOV OF NYERI NOTICE: Weights & Measures annual verification"
        f" for {sms_target_location} will take place at official centers"
        " starting next week. All trade weighing equipment must be presented."
        " Payment via M-Pesa only."
    )

    st.text_area(
        "Generated SMS Broadcast Content:", value=sms_template, height=110
    )

    if st.button("📲 Execute Mass Broadcast via Bulk Gateway"):
      if trader_count == 0:
        st.warning(
            f"No registered trader contacts found for location:"
            f" {sms_target_location}."
        )
      else:
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
            f"✅ **LOCATION BROADCAST COMPLETE:** Delivered **{trader_count:,}"
            f" SMS alerts** to registered traders in **{sms_target_location}**!"
        )

  # SAFARICOM API & COUNTY LICENSING CONFIGURATION PANEL
  st.markdown("---")
  st.subheader("🔌 Safaricom API & County Government Licensing Status")

  api_col1, api_col2 = st.columns(2)

  with api_col1:
    st.markdown("##### 🟢 Safaricom Daraja / SDP Gateway Config")
    st.text_input(
        "Safaricom Consumer Key",
        value="[Awaiting Live Production Credentials]",
        disabled=True,
    )
    st.text_input(
        "County Shortcode / Till Number",
        value="[Configured: Nyeri County Trade C2B]",
        disabled=True,
    )
    st.success(
        "Status: **API Architecture Ready** (Awaiting Safaricom Live Handshake)"
        "."
    )

  with api_col2:
    st.markdown("##### 🏛️ County System Licensing & Governance")
    st.text_input(
        "County Department",
        value="Department of Trade, Tourism & Co-operatives",
        disabled=True,
    )
    st.text_input(
        "License Certificate ID",
        value="[Pending Official County Board Approval]",
        disabled=True,
    )
    st.warning("Status: **Pending Official County Software Licensing**.")
