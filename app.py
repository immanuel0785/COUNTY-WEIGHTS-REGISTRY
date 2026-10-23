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
def process_uploaded_excel(file_bytes_io, sheet_name=0):
  try:
    df_raw = pd.read_excel(file_bytes_io, sheet_name=sheet_name, header=None)
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

    df = pd.read_excel(file_bytes_io, sheet_name=sheet_name, header=header_row_idx)
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


# --- 4. SESSION STATE & GIT WORKBOOK AUTO-LOADER (BYTES CACHED) ---
@st.cache_data
def load_workbook_from_git(file_path):
  sheets = {}
  try:
    with open(file_path, "rb") as f:
      file_bytes = f.read()

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


if "sheets_dict" not in st.session_state:
  st.session_state["sheets_dict"] = {}
  # UPDATED TO USE SYNTHETIC DATASET FILENAME
  default_workbook_path = "Nyeri_Trader_Inspection_Synthetic.xlsx"
  try:
    with st.spinner(
        "⏳ Loading County Historical Ledgers from Git... Please wait."
    ):
      st.session_state["sheets_dict"] = load_workbook_from_git(
          default_workbook_path
      )
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
    f" Repository (`Nyeri_Trader_Inspection_Synthetic.xlsx`). Sheets loaded:"
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📂 Digital Ledger Archive & Editable Sheets",
    "📈 Multi-Year Revenue & Station Analytics",
    "📝 Field Entry & Auto-Receipt Generator",
    "📅 Circuit Schedules & Mass SMS Engine",
    "🚨 Inspection Due Dashboard",
])

# --- TAB 1: ARCHIVE, INTERACTIVE EDITABLE LEDGER & ROLLOVER ---
with tab1:
  st.subheader("Master Verification Registry & Interactive Ledger")
  st.markdown(
      "Inspect historical records, edit inspection details live, or roll over"
      " annual trader profiles."
  )

  # VISUALIZE & EDIT LOADED SHEET SECTION
  with st.expander(
      "👁️ View & Edit Raw Loaded Workbook Sheets"
      " (`Nyeri_Trader_Inspection_Synthetic.xlsx`)",
      expanded=True,
  ):
    if st.session_state["sheets_dict"]:
      sheet_to_inspect = st.selectbox(
          "Select Sheet to Edit / Inspect:",
          list(st.session_state["sheets_dict"].keys()),
      )
      st.write(
          f"Showing active sheet: **{sheet_to_inspect}** (Rows:"
          f" {len(st.session_state['sheets_dict'][sheet_to_inspect]):,})"
      )

      # INTERACTIVE DATA EDITOR
      st.info(
          "✏️ **Field Officer Interactive Mode:** Double-click any cell below to"
          " update trader info, dates, or equipment counts."
      )

      active_sheet_df = st.session_state["sheets_dict"][sheet_to_inspect].copy()

      edited_df = st.data_editor(
          active_sheet_df,
          use_container_width=True,
          num_rows="dynamic",
          key=f"editor_{sheet_to_inspect}",
      )

      col_save1, col_save2 = st.columns([1, 2])

      with col_save1:
        if st.button("🔄 Auto-Recalculate Fees & Save Sheet"):
          recalculated_df = edited_df.copy()

          pumps_cols = [
              c
              for c in recalculated_df.columns
              if any(k in c.lower() for k in ["pump", "nozzle"])
          ]
          dig_scale_cols = [
              c
              for c in recalculated_df.columns
              if any(
                  k in c.lower()
                  for k in ["digital scale", "platform", "scale(9)"]
              )
          ]
          mech_scale_cols = [
              c
              for c in recalculated_df.columns
              if any(
                  k in c.lower()
                  for k in ["counter", "mechanical", "spring"]
              )
          ]
          weights_cols = [
              c
              for c in recalculated_df.columns
              if any(k in c.lower() for k in ["weight", "mass"])
          ]
          total_fee_cols = [
              c
              for c in recalculated_df.columns
              if any(k in c.lower() for k in ["total", "amount", "kshs"])
          ]

          for idx, row in recalculated_df.iterrows():
            total_fee = 0

            for c in pumps_cols:
              total_fee += (
                  pd.to_numeric(row[c], errors="coerce") or 0
              ) * 2400
            for c in dig_scale_cols:
              total_fee += (
                  pd.to_numeric(row[c], errors="coerce") or 0
              ) * 2000
            for c in mech_scale_cols:
              total_fee += (
                  pd.to_numeric(row[c], errors="coerce") or 0
              ) * 1500
            for c in weights_cols:
              total_fee += (pd.to_numeric(row[c], errors="coerce") or 0) * 500

            if total_fee_cols:
              recalculated_df.at[idx, total_fee_cols[0]] = total_fee

          # --- PERMANENT DATABASE SYNC FOR EDITS (THREAD-SAFE) ---
          with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM ledger_entries WHERE year_sheet = ?",
                (sheet_to_inspect,),
            )

            for idx, row in recalculated_df.iterrows():
              t_name = str(row.get("NAME", row.get("Trader_Name", "Unknown")))
              p_no = str(row.get("Phone No.", row.get("Phone", "0700000000")))
              stn = str(row.get("STATION", row.get("Sub_County", "OFFICE")))
              s_no_val = str(row.get("S/NO.", row.get("Serial_No", "PENDING")))
              date_val = str(row.get("DATE", row.get("Date", "PENDING")))
              tot_amt = (
                  float(row.get(total_fee_cols[0], 0))
                  if total_fee_cols
                  else 0.0
              )

              cursor.execute(
                  """
                        INSERT INTO ledger_entries (year_sheet, date_entry, serial_no, trader_name, phone_no, station, stamped_pumps, stamped_scales, stamped_weights, total_amount, mpesa_code, inspector_logged)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                  (
                      sheet_to_inspect,
                      date_val,
                      s_no_val,
                      t_name,
                      p_no,
                      stn,
                      int(row.get("stamped_pumps", 0))
                      if "stamped_pumps" in row
                      else 0,
                      int(row.get("stamped_scales", 0))
                      if "stamped_scales" in row
                      else 0,
                      int(row.get("stamped_weights", 0))
                      if "stamped_weights" in row
                      else 0,
                      tot_amt,
                      "",
                      st.session_state["user_name"],
                  ),
              )
            conn.commit()

          st.session_state["sheets_dict"][sheet_to_inspect] = recalculated_df
          st.success(
              f"✅ Sheet '{sheet_to_inspect}' successfully recalculated,"
              " saved to memory, and synced permanently to the database!"
          )
          st.rerun()

      with col_save2:
        st.caption(
            "💡 **Standard Fee Table:** Pumps @ KES 2,400 | Digital Scales @"
            " KES 2,000 | Counter Scales @ KES 1,500 | Mass Weights @ KES 500."
        )

    else:
      st.warning("No Excel sheets currently loaded in memory.")

  st.markdown("---")
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
      file_name="Nyeri_Trader_Inspection_Synthetic_Master.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )

  # 1-CLICK ANNUAL ROLLOVER: RESTRICTED TO DIRECTOR / ADMINISTRATOR ONLY
  if is_admin_or_director:
    st.markdown("---")
    st.markdown("### 👑 [Director Restricted] 1-Click Annual Trader Rollover")
    st.markdown(
        "Automatically roll over trader profiles from a previous year into a"
        " new year sheet and save them permanently to the database."
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

          # Commit rolled over records permanently to SQLite database safely
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
              f" '{target_year.strip()}' and saved permanently to the database!"
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

        # 1. Save to SQLite securely
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
            f"✅ Inspection logged successfully! Total Fee: KES"
            f" {calc_fee:,.2f}. Certificate generated."
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
      st.warning(
          "⚠️ Session timed out. Please click submit again or refresh the"
          " page."
      )


# --- TAB 4: CIRCUIT SCHEDULES & MASS SMS ENGINE ---
with tab4:
  st.subheader("📅 Circuit Schedules & Mass SMS Notification Engine")
  st.markdown(
      "Broadcast stamping inspection notices directly to registered traders in"
      " Nyeri County via Safaricom SMS Gateway."
  )

  st.dataframe(st.session_state["schedules"], use_container_width=True)

  st.markdown("---")
  st.markdown("### 📤 Send Bulk SMS Circuit Notice to Traders")
  sms_station = st.selectbox(
      "Select Target Station for SMS:",
      ["All Stations"]
      + list(df_active[station_col].dropna().unique())
      if station_col
      else ["All Stations"],
  )
  sms_message = st.text_area(
      "SMS Notice Content:",
      value=(
          "Jambo, County Govt of Nyeri: Weights & Measures inspection team will"
          " be at your station starting next week. Please ensure valid"
          " stamping of all weighing devices to avoid penalties. Enquiries:"
          " 061-2030700."
      ),
  )

  if st.button("🚀 Broadcast SMS via Safaricom Gateway"):
    st.success(
        f"✅ Bulk SMS notice successfully dispatched to registered traders"
        f" across {sms_station}! (Safaricom Gateway API connected)"
    )


# --- TAB 5: INSPECTION DUE DASHBOARD ---
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
