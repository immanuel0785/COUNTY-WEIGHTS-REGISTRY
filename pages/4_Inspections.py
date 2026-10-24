import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.db import save_record_to_db, load_all_db_records, load_traders_from_db
from src.receipts import generate_pdf_certificate
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
st.set_page_config(page_title="Inspections | Nyeri Registry", page_icon="⚖️", layout="wide")
st.title("📋 Field Verification & Inspection Workspace")
st.markdown("*Log active field stamping visits, calculate fees, process M-Pesa receipts, and auto-sync to DB.*")
st.markdown("---")

if "last_receipt_data" not in st.session_state:
    st.session_state["last_receipt_data"] = None

db_df = load_all_db_records()
default_sno = 204820
if not db_df.empty and 'serial_no' in db_df.columns:
    try:
        num_sno = pd.to_numeric(db_df['serial_no'], errors='coerce').dropna()
        if not num_sno.empty:
            default_sno = int(num_sno.max() + 1)
    except Exception:
        pass

registered_traders_df = load_traders_from_db()
trader_options = ["-- Select Registered Trader --"]
if not registered_traders_df.empty:
    trader_options.extend(registered_traders_df['trader_name'].dropna().unique().tolist())

with st.form("inspection_entry_form"):
    st.subheader("📝 Log Field Inspection & Issue Verification Receipt")
    f1, f2 = st.columns(2)
    
    with f1:
        st.text_input("Certificate Serial No. (S/NO.)", value=f"{default_sno}", disabled=True)
        selected_trader = st.selectbox("Select Registered Trader (or type manually below):", trader_options)
        manual_trader = st.text_input("Trader / Business Name", value="" if selected_trader != "-- Select Registered Trader --" else "", placeholder="e.g. KAMUNYI TRADERS")
        final_trader_name = selected_trader if selected_trader != "-- Select Registered Trader --" else manual_trader
        
        phone_no = st.text_input("Trader Phone Contact", placeholder="0722906936")
        station_val = st.selectbox("Station / Sub-County Location", [
            "NYERI TOWN", "OTHAYA", "MUKURWEINI", "TETU",
            "KIENI EAST", "KIENI WEST", "MATHIRA EAST", "MATHIRA WEST"
        ])
        insp_date = st.date_input("Inspection Date", value=datetime.today())
        
    with f2:
        stamped_pumps = st.number_input("Stamped Fuel Pumps (KES 2,400 ea)", min_value=0, value=1)
        stamped_scales = st.number_input("Stamped Scales (KES 2,000 ea)", min_value=0, value=0)
        stamped_weights = st.number_input("Stamped Weights (KES 500 ea)", min_value=0, value=0)
        mpesa_code = st.text_input("M-Pesa Confirmation Code", placeholder="e.g. QMC453ED1")

    submit_inspection = st.form_submit_button("Calculate Total, Save Entry & Sync Database")
    
    if submit_inspection:
        clean_code = mpesa_code.strip().upper()
        clean_phone = phone_no.strip() if phone_no.strip() != "" else "0700000000"
        calc_fee = (stamped_pumps * 2400) + (stamped_scales * 2000) + (stamped_weights * 500)
        if calc_fee == 0:
            calc_fee = 2000
            
        if final_trader_name.strip() == "":
            st.warning("Please enter or select a valid Trader / Business Name.")
        elif len(clean_code) < 8:
            st.error("⚠️ Valid M-Pesa transaction code is required.")
        else:
            date_str = insp_date.strftime("%Y-%m-%d")
            due_str = (insp_date + timedelta(days=365)).strftime("%Y-%m-%d")
            
            rec_payload = {
                "year_sheet": "2026",
                "s_no": default_sno,
                "trader": final_trader_name.strip().upper(),
                "phone": clean_phone,
                "station": station_val,
                "pumps": stamped_pumps,
                "scales": stamped_scales,
                "weights": stamped_weights,
                "fee": calc_fee,
                "code": clean_code,
                "date": date_str,
                "due": due_str,
                "inspector": "Insp. Field Officer"
            }
            
            save_record_to_db(rec_payload)
            st.session_state["last_receipt_data"] = rec_payload
            st.success(f"✅ Verification Logged & Synced to DB! Total Paid: KES {calc_fee:,.2f}")
            st.rerun()

if st.session_state["last_receipt_data"]:
    r = st.session_state["last_receipt_data"]
    st.markdown("---")
    st.subheader("📄 Official Verification Certificate Preview")
    try:
        pdf_bytes = generate_pdf_certificate(r)
        st.download_button(
            label="📥 Download Printable Verification Certificate (.pdf)",
            data=pdf_bytes,
            file_name=f"Certificate_{r['s_no']}_{r['trader'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    except Exception:
        pass
