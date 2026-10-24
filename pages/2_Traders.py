import streamlit as st
from src.db import save_trader_to_db, load_traders_from_db
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
st.set_page_config("Trader Registry | Nyeri Registry")
st.title("👥 Trader & Business Registry")
st.markdown("*Register new businesses and manage verified contact directories.*")
st.markdown("---")

t_tab1, t_tab2 = st.tabs(["➕ Register New Trader", "📂 View Registered Traders Directory"])

with t_tab1:
    st.subheader("Add New Trader / Business Profile")
    with st.form("trader_reg_form"):
        c1, c2 = st.columns(2)
        with c1:
            t_name = st.text_input("Business / Trader Name *", placeholder="e.g. DEKUT COFFEE MILLERS")
            t_phone = st.text_input("Primary Contact Phone *", placeholder="0722000111")
            t_station = st.selectbox("Sub-County / Station *", [
                "NYERI TOWN", "OTHAYA", "MUKURWEINI", "TETU",
                "KIENI EAST", "KIENI WEST", "MATHIRA EAST", "MATHIRA WEST"
            ])
        with c2:
            t_cat = st.selectbox("Trade Category", [
                "Petrol Station / Fuel Depot", "Retail Shop / Butchery",
                "Supermarket / Wholesale", "Coffee / Tea Factory", "Hardware / Agri-Vet"
            ])
            t_address = st.text_input("Physical Address / Plot No.", placeholder="e.g. Main Street, Plot 14")
            t_officer = st.text_input("Registering Officer", value="Insp. Ndirangu")
            
        reg_btn = st.form_submit_button("Register Trader into Central DB")
        if reg_btn:
            if t_name.strip() == "" or t_phone.strip() == "":
                st.error("⚠️ Please fill in all required fields (Trader Name & Phone).")
            else:
                success, msg = save_trader_to_db(t_name.strip().upper(), t_phone.strip(), t_station, t_cat, t_address.strip(), t_officer)
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"⚠️ {msg}")

with t_tab2:
    st.subheader("Registered Traders Ledger")
    traders_df = load_traders_from_db()
    if not traders_df.empty:
        search_t = st.text_input("Filter by trader name, phone or station:", placeholder="Search...")
        if search_t:
            mask = traders_df.astype(str).apply(lambda x: x.str.contains(search_t, case=False, na=False))
            traders_df = traders_df[mask.any(axis=1)]
        st.dataframe(traders_df, use_container_width=True)
    else:
        st.info("No registered traders found in DB yet. Add one above!")
