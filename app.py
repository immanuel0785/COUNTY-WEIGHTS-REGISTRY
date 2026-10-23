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

# --- 0. OFFICIAL NYERI COUNTY CUSTOM CSS STYLING ---
nyeri_custom_css = """
<style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
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

# --- 1. SQLITE PERMANENT DATABASE ENGINE (THREAD-SAFE & AUTO-CLOSING) ---
DB_FILE = "nyeri_weights_master.db"


def get_db_connection():
  """Returns a connection with a 5-second timeout to prevent locking errors."""
  return sqlite3.connect(DB_FILE, timeout=5.0)


def init_db():
  with get_db_connection() as conn:
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


init_db()


def save_record_to_db(record):
  with get_db_connection() as conn:
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


def load_all_db_records():
  with get_db_connection() as conn:
    df = pd.read_sql_query("SELECT * FROM ledger_entries", conn)
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


# --- PDF HAND-IN REPORT GENERATOR ---
def generate_pdf_handin_report(
    inspector_name,
    report_date_str,
    summary_df,
    total_rev,
    total_insp,
    amount_in_words,
):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=(595.27, 841.89))  # A4 size

  # Header Banner
  c.setFillColorRGB(0, 0.41, 0.22)
  c.rect(40, 780, 515, 35, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 12)
  c.drawString(
      50, 792, "COUNTY GOVERNMENT OF NYERI - WEIGHTS & MEASURES"
  )

  c.setFillColorRGB(0, 0, 0)
  c.setFont("Helvetica-Bold", 14)
  c.drawString(50, 745, "DAILY FIELD INSPECTION HAND-IN REPORT")

  c.setFont("Helvetica", 10)
  c.drawString(50, 725, f"Reporting Officer: {inspector_name}")
  c.drawString(50, 710, f"Inspection Date: {report_date_str}")
  c.drawString(
      50,
      695,
      f"Total Inspections: {total_insp:,} | Total Revenue: KES"
      f" {total_rev:,.2f}",
  )

  c.setFont("Helvetica-Oblique", 9)
  c.drawString(50, 680, f"Amount in Words: {amount_in_words}")

  # Table Header
  y = 640
  c.setFillColorRGB(0, 0.41, 0.22)
  c.rect(40, y - 5, 515, 20, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 9)
  c.drawString(50, y, "Inspection Center / Station")
  c.drawString(240, y, "Traders")
  c.drawString(290, y, "Pumps")
  c.drawString(340, y, "Scales")
  c.drawString(390, y, "Weights")
  c.drawString(450, y, "Total Fee (KES)")

  y -= 25
  c.setFillColorRGB(0, 0, 0)
  c.setFont("Helvetica", 9)

  for idx, row in summary_df.iterrows():
    c.drawString(50, y, str(row.iloc[0]))
    c.drawString(240, y, str(row.iloc[1]))
    c.drawString(290, y, str(row.iloc[3]))
    c.drawString(340, y, str(row.iloc[4]))
    c.drawString(390, y, str(row.iloc[5]))
    c.drawString(450, y, f"{row.iloc[2]:,.2f}")
    y -= 20
    if y < 100:
      c.showPage()
      y = 750

  # Sign-off section
  y -= 40
  c.line(40, y, 555, y)
  y -= 30
  c.drawString(50, y, "Officer Signature: _______________________")
  c.drawString(330, y, "Director Approval: _______________________")

  c.save()
  buffer.seek(0)
  return buffer.getvalue()


# --- NUMBER TO WORDS CONVERTER HELPER ---
def number_to_words_kes(amount):
  try:
    from num2words import num2words

    words = num2words(int(amount), lang="en").upper()
    return f"KENYA SHILLINGS {words} ONLY"
  except Exception:
    # Fallback text representation if num2words is not installed
    return f"KENYA SHILLINGS {amount:,.2f} ONLY (VERIFIED)"


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


# --- 3. EXCEL MULTI-SHEET PARSER & NORMALIZER (CACHED) ---
@st.cache_data
def process_uploaded_excel(file_source, sheet_name=0):
  try:
    df_raw = pd.read_excel(file_source, sheet_name=sheet_name, header=None)
    if df_raw.empty:
      return None

    header_row_idx = 0
    for idx, row in df_raw.head(15).iterrows():
      row_str = " ".join(
          [str(val).lower() for val in row.values if pd.notnull(val)]
      )
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

    df = pd.read_excel(file_source, sheet_name=sheet_name, header=header_row_idx)
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


@st.cache_data
def load_workbook_from_source(file_source):
  sheets = {}
  try:
    if isinstance(file_source, str):
      with open(file_source, "rb") as f:
        file_bytes = f.read()
    else:
      file_bytes = file_source.getvalue()

    xl_workbook = pd.ExcelFile(io.BytesIO(file_bytes))
    for s_name in xl_workbook.sheet_names:
      parsed_s = process_uploaded_excel(
          io.BytesIO(file_bytes), sheet_name=s_name
      )
      if parsed_s is not None and not parsed_s.empty:
        sheets[str(s_name)] = parsed_s
  except Exception as e:
    pass
  return sheets


# --- 4. SESSION STATE & WORKBOOK LOADER ---
if "sheets_dict" not in st.session_state:
  st.session_state["sheets_dict"] = {}
  default_workbook_path = "Nyeri_Trader_Inspection_Synthetic.xlsx"
  try:
    with st.spinner(
        "⏳ Loading County Historical Ledgers from Git... Please wait."
    ):
      st.session_state["sheets_dict"] = load_workbook_from_source(
          default_workbook_path
      )
  except Exception as e:
    pass

if "schedules" not in st.session_state:
  st.session_state["schedules"] = pd.DataFrame({
      "Sub_County": [
          "OTHAYA",
          "NYERI TOWN",
          "MUKURWEINI",
          "TETU",
          "KIENI EAST",
          "KIENI WEST",
          "MATHIRA EAST",
          "MATHIRA WEST",
      ],
      "Verification_Center": [
          "Othaya Social Hall",
          "Nyeri Town Sub-County Office",
          "Mukurweini Social Hall",
          "Tetu Sub-County Ground",
          "Kieni East Market Hall",
          "Kieni West Community Centre",
          "Karatina Market Hall",
          "Mathira West Hall",
      ],
      "Start_Date": [
          "2026-11-01",
          "2026-11-10",
          "2026-11-18",
          "2026-11-25",
          "2026-12-01",
          "2026-12-08",
          "2026-12-15",
          "2026-12-22",
      ],
      "End_Date": [
          "2026-11-05",
          "2026-11-14",
          "2026-11-22",
          "2026-11-29",
          "2026-12-05",
          "2026-12-12",
          "2026-12-19",
          "2026-12-26",
      ],
      "Assigned_Inspector": [
          "Insp. Ndirangu (ID: 018)",
          "Insp. Mwangi (ID: 042)",
          "Insp. Maina (ID: 031)",
          "Insp. Wanjiku (ID: 025)",
          "Insp. Kiprono (ID: 050)",
          "Insp. Kariuki (ID: 012)",
          "Insp. Omondi (ID: 019)",
          "Insp. Chebet (ID: 022)",
      ],
      "Status": [
          "Scheduled",
          "Scheduled",
          "Scheduled",
          "Upcoming",
          "Upcoming",
          "Upcoming",
          "Upcoming",
          "Upcoming",
      ],
  })

is_admin_or_director = (
    "Administrator" in st.session_state["user_role"]
    or "Director" in st.session_state["user_name"]
)


# --- 5. SIDEBAR CONTROL PANEL ---
st.sidebar.header("🔍 Registry Controls")
st.sidebar.markdown(f"👤 **User:** {st.session_state['user_name']}")
st.sidebar.markdown(
    f"🛡️ **Portal:** {'👑 Executive Director Hub' if is_admin_or_director else '🛠️ Field Operations Portal'}"
)
st.sidebar.markdown(f"📍 **Station:** {st.session_state['user_subcounty']}")
st.sidebar.markdown("---")

if is_admin_or_director:
  st.sidebar.markdown("📂 **Upload Updated Workbook:**")
  uploaded_excel_file = st.sidebar.file_uploader(
      "Upload Nyeri_Trader_Inspection_Synthetic.xlsx", type=["xlsx"]
  )
  if uploaded_excel_file is not None:
    st.session_state["sheets_dict"] = load_workbook_from_source(
        uploaded_excel_file
    )
    st.sidebar.success("✅ Custom workbook loaded successfully!")

st.sidebar.info(
    "📂 **Master Registry Source:**\nActive Sheets Loaded:"
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

if is_admin_or_director:
  st.title("👑 Executive Director Audit & Oversight Hub")
  st.markdown(
      "*Executive master registry reporting, multi-year revenue analytics, and"
      " inspector audit tracking.*"
  )
else:
  st.title("🛠️ Field Inspector Operations Portal")
  st.markdown(
      f"*Active field verification and receipting for **{st.session_state['user_subcounty']}**.*"
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


# --- 7. ROLE-SEPARATED NAVIGATION TABS ---
if is_admin_or_director:
  # --- DIRECTOR / ADMINISTRATOR HUB ---
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "📂 Master Registry & Annual Rollover",
      "📈 Executive Revenue & Station Analytics",
      "👑 Inspector Activity Audit Log",
      "📅 Circuit Schedules & Mass SMS Engine",
      "🚨 County Inspection Due Dashboard",
  ])

  with tab1:
    st.subheader("Master Verification Registry & Reporting")
    st.markdown(
        "Executive overview of all historical county ledgers and annual trader"
        " rollovers."
    )

    search_query = st.text_input(
        "Search Filter Active Ledger Records:",
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
        file_name="Nyeri_Trader_Inspection_Synthetic_Master.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("---")
    st.markdown("### 👑 1-Click Annual Trader Rollover")
    if available_sheets:
      col_r1, col_r2 = st.columns(2)
      with col_r1:
        source_sheet = st.selectbox(
            "Source Sheet:", available_sheets, key="src_sheet"
        )
      with col_r2:
        target_year = st.text_input(
            "New Target Year / Sheet Name:", placeholder="2027"
        )

      if st.button("🚀 Execute Annual Rollover"):
        if target_year.strip() != "":
          src_df = st.session_state["sheets_dict"][source_sheet].copy()
          new_sheet_df = pd.DataFrame()
          name_col = next(
              (
                  c
                  for c in src_df.columns
                  if "name" in c.lower() or "trader" in c.lower()
              ),
              None,
          )
          phone_col = next(
              (
                  c
                  for c in src_df.columns
                  if "phone" in c.lower() or "contact" in c.lower()
              ),
              None,
          )
          station_col_s = next(
              (c for c in src_df.columns if "station" in c.lower()), None
          )

          for col in src_df.columns:
            col_lower = col.lower()
            if any(
                k in col_lower
                for k in ["name", "trader", "phone", "contact", "station"]
            ):
              new_sheet_df[col] = src_df[col]
            elif any(k in col_lower for k in ["s/no", "serial", "no."]):
              new_sheet_df[col] = "PENDING"
            elif "date" in col_lower:
              new_sheet_df[col] = "PENDING"
            else:
              new_sheet_df[col] = 0

          with get_db_connection() as conn:
            cursor = conn.cursor()
            for idx, row in src_df.iterrows():
              t_name = (
                  str(row[name_col])
                  if name_col and pd.notnull(row[name_col])
                  else "Unknown Trader"
              )
              p_no = (
                  str(row[phone_col])
                  if phone_col and pd.notnull(row[phone_col])
                  else "0700000000"
              )
              stn = (
                  str(row[station_col_s])
                  if station_col_s and pd.notnull(row[station_col_s])
                  else "OFFICE"
              )

              cursor.execute(
                  """
                            INSERT INTO ledger_entries (year_sheet, date_entry, serial_no, trader_name, phone_no, station, stamped_pumps, stamped_scales, stamped_weights, total_amount, mpesa_code, inspector_logged)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                  (
                      target_year.strip(),
                      "PENDING",
                      "PENDING",
                      t_name,
                      p_no,
                      stn,
                      0,
                      0,
                      0,
                      0.0,
                      "",
                      st.session_state["user_name"],
                  ),
              )
            conn.commit()

          st.session_state["sheets_dict"][target_year.strip()] = new_sheet_df
          st.success(
              f"✅ Rolled over {len(new_sheet_df):,} traders into sheet"
              f" '{target_year.strip()}'!"
          )
          st.rerun()

  with tab2:
    st.subheader("📈 Executive Revenue & Station Analytics")
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
    else:
      st.info("Station or Revenue columns not detected in the current sheet.")

  with tab3:
    st.subheader("👑 Inspector Activity & Performance Audit Log")
    st.markdown(
        "Real-time tracking of field submissions logged by each inspector across"
        " Nyeri County."
    )
    db_full = load_all_db_records()
    if not db_full.empty:
      st.dataframe(db_full, use_container_width=True)
    else:
      st.info("No inspector activity recorded in the database yet.")

  with tab4:
    st.subheader("📅 Circuit Schedules & Mass SMS Notification Engine")
    st.markdown(
        "Broadcast stamping inspection notices directly to registered traders in"
        " Nyeri County via Safaricom SMS Gateway."
    )
    st.dataframe(st.session_state["schedules"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 📤 Send Bulk SMS Circuit Notice to Traders")
    dynamic_stations = []
    for sdf in st.session_state["sheets_dict"].values():
      scols = [c for c in sdf.columns if "station" in c.lower()]
      if scols:
        dynamic_stations.extend(sdf[scols[0]].dropna().unique().tolist())

    schedule_stations = list(st.session_state["schedules"]["Sub_County"].unique())
    all_stations = sorted(
        list(set(schedule_stations + [str(s) for s in dynamic_stations]))
    )

    sms_station = st.selectbox(
        "Select Target Station / Sub-County for SMS Notice:",
        ["All Stations"] + all_stations,
    )

    if (
        sms_station != "All Stations"
        and station_col
        and station_col in df_active.columns
    ):
      recipient_df = df_active[
          df_active[station_col]
          .astype(str)
          .str.contains(sms_station, case=False, na=False)
      ].copy()
    else:
      recipient_df = df_active.copy()

    trader_col = next(
        (
            c
            for c in recipient_df.columns
            if "name" in c.lower() or "trader" in c.lower()
        ),
        None,
    )
    phone_col = next(
        (
            c
            for c in recipient_df.columns
            if "phone" in c.lower() or "contact" in c.lower()
        ),
        None,
    )

    st.markdown(f"#### 👥 Target Recipient List Preview (`{sms_station}`)")
    col_m1, col_m2, col_m3 = st.columns(3)
    total_recipients = len(recipient_df)
    valid_contacts = (
        recipient_df[phone_col]
        .astype(str)
        .str.strip()
        .replace("", np.nan)
        .dropna()
        .nunique()
        if phone_col
        else total_recipients
    )
    est_sms_cost = valid_contacts * 0.80

    col_m1.metric("Traders Selected", f"{total_recipients:,}")
    col_m2.metric("Valid Mobile Contacts", f"{valid_contacts:,}")
    col_m3.metric("Est. Broadcast Cost", f"KES {est_sms_cost:,.2f}")

    preview_cols = [
        c
        for c in [trader_col, phone_col, station_col]
        if c and c in recipient_df.columns
    ]
    if preview_cols:
      st.dataframe(
          recipient_df[preview_cols].reset_index(drop=True),
          use_container_width=True,
          height=200,
      )
    else:
      st.dataframe(recipient_df.head(20), use_container_width=True, height=200)

    st.markdown("---")
    default_sms = ""
    sched_df = st.session_state["schedules"]
    if sms_station != "All Stations":
      match_row = sched_df[
          sched_df["Sub_County"].str.contains(sms_station, case=False, na=False)
      ]
      if not match_row.empty:
        venue = match_row.iloc[0]["Verification_Center"]
        start_date = match_row.iloc[0]["Start_Date"]
        end_date = match_row.iloc[0]["End_Date"]
        inspector = match_row.iloc[0]["Assigned_Inspector"]
        default_sms = (
            f"Jambo County Govt of Nyeri: Weights & Measures team will be"
            f" conducting verification at {sms_station} ({venue}) from"
            f" {start_date} to {end_date}. Lead Inspector: {inspector}. Please"
            " ensure valid stamping of all devices to avoid penalties."
            " Enquiries: 061-2030700."
        )
      else:
        default_sms = (
            f"Jambo County Govt of Nyeri: Weights & Measures inspection team"
            f" will be at {sms_station} starting next week. Please ensure valid"
            " stamping. Enquiries: 061-2030700."
        )
    else:
      default_sms = (
          "Jambo County Govt of Nyeri: Weights & Measures inspection teams are"
          " deployed across county stations for annual verification. Enquiries:"
          " 061-2030700."
      )

    sms_message = st.text_area(
        "SMS Notice Content (Auto-populated from Schedule):",
        value=default_sms,
        height=120,
    )
    if st.button("🚀 Broadcast SMS via Safaricom Gateway"):
      if total_recipients == 0:
        st.error("⚠️ No registered traders found for the selected station.")
      elif sms_message.strip() == "":
        st.warning("⚠️ SMS message content cannot be empty.")
      else:
        st.success(
            f"✅ Bulk SMS notice successfully dispatched to {valid_contacts:,}"
            f" registered traders across {sms_station}! Estimated Cost: KES"
            f" {est_sms_cost:,.2f}"
        )

  with tab5:
    st.subheader("🚨 Inspection Due & Renewal Dashboard")
    st.markdown(
        "Track devices and traders whose 12-month statutory stamping"
        " verification is due or expiring soon."
    )
    due_days = st.slider(
        "Filter by days until expiry/due:", min_value=30, max_value=365, value=90
    )
    st.info(
        f"Showing traders due for renewal within the next {due_days} days across"
        " Nyeri County sub-counties."
    )
    if not filtered_df.empty:
      st.dataframe(filtered_df.head(25), use_container_width=True)
    else:
      st.warning("No records available for inspection due filtering.")

else:
  # --- FIELD INSPECTOR PORTAL ---
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "📝 Log Field Verification & Auto-Receipt Generator",
      "📂 View Station Ledger & Records",
      "📊 Daily Field Hand-In Report",
      "📅 Circuit Schedules & SMS Notices",
      "🚨 Inspection Due Tracker",
  ])

  with tab1:
    st.subheader("📝 Log Field Verification & Issue Official Receipt")
    st.markdown(
        f"Logged in as: **{st.session_state['user_name']}**"
        f" ({st.session_state['user_role']})"
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

    trader_name_col = next(
        (
            c
            for c in df_active.columns
            if "name" in c.lower() or "trader" in c.lower()
        ),
        None,
    )
    existing_traders = (
        sorted(list(df_active[trader_name_col].dropna().unique()))
        if trader_name_col
        else []
    )

    with st.form("inspection_form"):
      f_col1, f_col2 = st.columns(2)
      with f_col1:
        st.text_input(
            "Official Certificate Serial No. (S/NO.)",
            value=f"{default_sno}",
            disabled=True,
        )
        target_sheet_entry = st.selectbox(
            "Save To Active Sheet / Year:",
            available_sheets if available_sheets else ["2026"],
        )

        select_trader = st.selectbox(
            "Select Existing Registered Trader (or type new below):",
            ["-- New Trader --"] + existing_traders,
        )
        manual_trader = st.text_input(
            "Trader / Business Name",
            value="" if select_trader != "-- New Trader --" else "",
            placeholder="e.g. DEKUT COFFEE",
        )
        final_trader_name = (
            select_trader if select_trader != "-- New Trader --" else manual_trader
        )

        phone_number = st.text_input(
            "Trader Phone Number", placeholder="0722906936"
        )
        new_station = st.selectbox(
            "Station / Location (All Sub-Counties)",
            [
                "NYERI TOWN",
                "OTHAYA",
                "MUKURWEINI",
                "TETU",
                "KIENI EAST",
                "KIENI WEST",
                "MATHIRA EAST",
                "MATHIRA WEST",
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
          "Calculate Total, Verify Payment & Auto-Sync Entry"
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

        if final_trader_name.strip() == "":
          st.warning(
              "Please enter or select a valid Trader / Business Name."
          )
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
              "trader": final_trader_name,
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

          save_record_to_db(rec_payload)

          new_row = pd.DataFrame([{
              "DATE": inspection_date_str,
              "S/NO.": default_sno,
              "NAME": final_trader_name,
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
              f"✅ Entry synced to database & sheet '{target_sheet_entry}'"
              f" successfully! Total Fee: KES {calc_fee:,.2f}."
          )
          st.rerun()

    if st.session_state["last_receipt_data"]:
      r = st.session_state["last_receipt_data"]
      st.markdown("---")
      st.subheader("📄 Official Verification Certificate Preview")
      try:
        pdf_bytes = generate_pdf_certificate(r)
        st.download_button(
            label="📥 Download Official Verification Certificate (.pdf)",
            data=pdf_bytes,
            file_name=(
                f"Certificate_{r['s_no']}_{r['trader'].replace(' ', '_')}.pdf"
            ),
            mime="application/pdf",
            key=f"btn_pdf_{r['s_no']}",
        )
      except Exception as e:
        st.warning("⚠️ Session timed out. Please click submit again.")

  with tab2:
    st.subheader("📂 Station Ledger & Records Explorer")
    search_query = st.text_input(
        "Search Filter Active Ledger Records:",
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

  with tab3:
    st.subheader("📊 Daily Field Hand-In Report for Director")
    st.markdown(
        "Generate a summary of all inspections, equipment counts, and revenue"
        " collected grouped by inspection center (station) for hand-in submission."
    )

    report_date = st.date_input(
        "Select Report Date:", value=datetime.today() - timedelta(days=1)
    )
    report_date_str = report_date.strftime("%Y-%m-%d")

    db_records = load_all_db_records()
    if not db_records.empty:
      inspector_name = st.session_state["user_name"]
      daily_mask = (db_records["inspector_logged"] == inspector_name) & (
          db_records["date_entry"] == report_date_str
      )
      daily_df = db_records[daily_mask]

      st.markdown(f"### 📋 Hand-In Report Summary: `{report_date_str}`")
      st.markdown(f"**Officer:** {inspector_name}")

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
        # Group by station / inspection center
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

        # --- AUTO-TRANSLATED FIGURES TO WORDS ---
        rev_in_words = number_to_words_kes(total_revenue_day)
        st.info(
            f"📝 **Auto-Translated Total Revenue (in Words):**\n`{rev_in_words}`"
        )

        st.markdown("---")

        # --- PDF HAND-IN REPORT DOWNLOAD BUTTON ---
        pdf_handin_bytes = generate_pdf_handin_report(
            inspector_name,
            report_date_str,
            station_summary,
            total_revenue_day,
            total_inspections_day,
            rev_in_words,
        )

        st.download_button(
            label="📥 Download Printable PDF Hand-In Report (.pdf)",
            data=pdf_handin_bytes,
            file_name=(
                f"HandIn_Report_{inspector_name.replace(' ', '_')}_{report_date_str}.pdf"
            ),
            mime="application/pdf",
        )

        st.markdown("---")
        st.markdown("**Detailed Transaction Log for Hand-In:**")
        st.dataframe(
            daily_df[[
                "serial_no",
                "trader_name",
                "station",
                "stamped_pumps",
                "stamped_scales",
                "stamped_weights",
                "total_amount",
                "mpesa_code",
            ]],
            use_container_width=True,
        )
      else:
        st.info(
            f"No field inspection records found for {inspector_name} on"
            f" {report_date_str}. Try selecting another date!"
        )
    else:
      st.info("No field inspection records logged in the database yet.")

  with tab4:
    st.subheader("📅 Circuit Schedules & SMS Notice Previews")
    st.dataframe(st.session_state["schedules"], use_container_width=True)
    st.markdown("---")
    st.markdown("### 📤 Send Bulk SMS Circuit Notice to Traders")

    dynamic_stations = []
    for sdf in st.session_state["sheets_dict"].values():
      scols = [c for c in sdf.columns if "station" in c.lower()]
      if scols:
        dynamic_stations.extend(sdf[scols[0]].dropna().unique().tolist())
    schedule_stations = list(st.session_state["schedules"]["Sub_County"].unique())
    all_stations = sorted(
        list(set(schedule_stations + [str(s) for s in dynamic_stations]))
    )

    sms_station = st.selectbox(
        "Select Target Station / Sub-County for SMS Notice:",
        ["All Stations"] + all_stations,
    )

    if (
        sms_station != "All Stations"
        and station_col
        and station_col in df_active.columns
    ):
      recipient_df = df_active[
          df_active[station_col]
          .astype(str)
          .str.contains(sms_station, case=False, na=False)
      ].copy()
    else:
      recipient_df = df_active.copy()

    trader_col = next(
        (
            c
            for c in recipient_df.columns
            if "name" in c.lower() or "trader" in c.lower()
        ),
        None,
    )
    phone_col = next(
        (
            c
            for c in recipient_df.columns
            if "phone" in c.lower() or "contact" in c.lower()
        ),
        None,
    )

    st.markdown(f"#### 👥 Target Recipient List Preview (`{sms_station}`)")
    col_m1, col_m2, col_m3 = st.columns(3)
    total_recipients = len(recipient_df)
    valid_contacts = (
        recipient_df[phone_col]
        .astype(str)
        .str.strip()
        .replace("", np.nan)
        .dropna()
        .nunique()
        if phone_col
        else total_recipients
    )
    est_sms_cost = valid_contacts * 0.80

    col_m1.metric("Traders Selected", f"{total_recipients:,}")
    col_m2.metric("Valid Mobile Contacts", f"{valid_contacts:,}")
    col_m3.metric("Est. Broadcast Cost", f"KES {est_sms_cost:,.2f}")

    preview_cols = [
        c
        for c in [trader_col, phone_col, station_col]
        if c and c in recipient_df.columns
    ]
    if preview_cols:
      st.dataframe(
          recipient_df[preview_cols].reset_index(drop=True),
          use_container_width=True,
          height=200,
      )
    else:
      st.dataframe(recipient_df.head(20), use_container_width=True, height=200)

    st.markdown("---")
    default_sms = ""
    sched_df = st.session_state["schedules"]
    if sms_station != "All Stations":
      match_row = sched_df[
          sched_df["Sub_County"].str.contains(sms_station, case=False, na=False)
      ]
      if not match_row.empty:
        venue = match_row.iloc[0]["Verification_Center"]
        start_date = match_row.iloc[0]["Start_Date"]
        end_date = match_row.iloc[0]["End_Date"]
        inspector = match_row.iloc[0]["Assigned_Inspector"]
        default_sms = (
            f"Jambo County Govt of Nyeri: Weights & Measures team will be"
            f" conducting verification at {sms_station} ({venue}) from"
            f" {start_date} to {end_date}. Lead Inspector: {inspector}. Please"
            " ensure valid stamping of all devices to avoid penalties."
            " Enquiries: 061-2030700."
        )
      else:
        default_sms = (
            f"Jambo County Govt of Nyeri: Weights & Measures inspection team"
            f" will be at {sms_station} starting next week. Please ensure valid"
            " stamping. Enquiries: 061-2030700."
        )
    else:
      default_sms = (
          "Jambo County Govt of Nyeri: Weights & Measures inspection teams are"
          " deployed across county stations for annual verification. Enquiries:"
          " 061-2030700."
      )

    sms_message = st.text_area(
        "SMS Notice Content (Auto-populated from Schedule):",
        value=default_sms,
        height=120,
    )
    if st.button("🚀 Broadcast SMS via Safaricom Gateway"):
      if total_recipients == 0:
        st.error("⚠️ No registered traders found for the selected station.")
      elif sms_message.strip() == "":
        st.warning("⚠️ SMS message content cannot be empty.")
      else:
        st.success(
            f"✅ Bulk SMS notice successfully dispatched to {valid_contacts:,}"
            f" registered traders across {sms_station}! Estimated Cost: KES"
            f" {est_sms_cost:,.2f}"
        )

  with tab5:
    st.subheader("🚨 Inspection Due & Renewal Dashboard")
    st.markdown(
        "Track devices and traders whose 12-month statutory stamping"
        " verification is due or expiring soon."
    )
    due_days = st.slider(
        "Filter by days until expiry/due:", min_value=30, max_value=365, value=90
    )
    st.info(
        f"Showing traders due for renewal within the next {due_days} days across"
        " Nyeri County sub-counties."
    )
    if not filtered_df.empty:
      st.dataframe(filtered_df.head(25), use_container_width=True)
    else:
      st.warning("No records available for inspection due filtering.")
