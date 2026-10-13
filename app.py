import numpy as np
import pandas as pd
import streamlit as st

# Configure page layout
st.set_page_config(
    page_title='County Weights & Measures Digital Registry',
    page_icon='⚖️',
    layout='wide',
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
  traders = [
      f'Trader_{np.random.randint(1000, 9999)}' for _ in range(n_rows)
  ]
  sub_counties = np.random.choice(
      ['Central Ward', 'North Sub-County', 'South Market', 'East Division'],
      size=n_rows,
  )
  equipment = np.random.choice(
      [
          'Counter Scale',
          'Platform Scale',
          'Fuel Dispenser',
          'Spring Balance',
          'Mass Piece',
      ],
      size=n_rows,
      p=[0.4, 0.2, 0.15, 0.15, 0.1],
  )
  status = np.random.choice(
      ['Passed', 'Rejected', 'Conditional Pass'], size=n_rows, p=[0.72, 0.20, 0.08]
  )
  fees = np.where(
      status == 'Passed',
      np.random.choice([1500, 3000, 5000], size=n_rows),
      np.random.choice([500, 1000], size=n_rows),
  )

  df = pd.DataFrame({
      'Year': years,
      'Trader_Name': traders,
      'Sub_County': sub_counties,
      'Equipment_Type': equipment,
      'Inspection_Status': status,
      'Fee_Collected': fees,
  })
  return df


# Initialize Session State so added entries persist across actions
if 'df' not in st.session_state:
  st.session_state['df'] = load_mock_data()

df = st.session_state['df']

# --- 2. SIDEBAR FILTERS (The Control Panel) ---
st.sidebar.header('🔍 Registry Filter Controls')

selected_years = st.sidebar.slider(
    'Select Year Range', 2015, 2026, (2015, 2026)
)
selected_subcounty = st.sidebar.selectbox(
    'Filter by Region', ['All'] + list(df['Sub_County'].unique())
)
selected_status = st.sidebar.selectbox(
    'Compliance Status', ['All'] + list(df['Inspection_Status'].unique())
)

# Apply filters
filtered_df = df[
    (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1])
]
if selected_subcounty != 'All':
  filtered_df = filtered_df[filtered_df['Sub_County'] == selected_subcounty]
if selected_status != 'All':
  filtered_df = filtered_df[filtered_df['Inspection_Status'] == selected_status]

# --- 3. MAIN DASHBOARD HEADER ---
st.title('⚖️ County Weights & Measures Digital Transformation Hub')
st.markdown(
    '*Replacing manual paper records with real-time analytics, rapid lookups,'
    ' and cashless M-Pesa revenue tracking (2015–2026).*'
)
st.markdown('---')

# --- 4. TOP-LEVEL METRICS (KPIs) ---
total_inspections = len(filtered_df)
total_revenue = filtered_df['Fee_Collected'].sum()
compliance_rate = (
    (
        len(filtered_df[filtered_df['Inspection_Status'] == 'Passed'])
        / total_inspections
        * 100
    )
    if total_inspections > 0
    else 0
)

col1, col2, col3 = st.columns(3)
col1.metric('Total Inspections Logged', f'{total_inspections:,}')
col2.metric('Estimated Revenue Collected', f'KES {total_revenue:,.2f}')
col3.metric('Compliance Rate', f'{compliance_rate:.1f}%')

st.markdown('---')

# --- 5. TABS FOR ORGANIZED NAVIGATION ---
tab1, tab2, tab3 = st.tabs([
    '📈 Trends & Analytics',
    '📂 Digital Archive (Search)',
    '📝 Field Inspection Portal (Cashless)',
])

with tab1:
  st.subheader('Historical Inspection & Revenue Growth')

  col_a, col_b = st.columns(2)

  with col_a:
    st.markdown('**Inspections per Year**')
    yearly_counts = filtered_df.groupby('Year').size()
    st.bar_chart(yearly_counts)

  with col_b:
    st.markdown('**Revenue Collected per Year (KES)**')
    yearly_revenue = filtered_df.groupby('Year')['Fee_Collected'].sum()
    st.line_chart(yearly_revenue)

with tab2:
  st.subheader('Master Database Lookup (Replaces Physical Books)')
  search_query = st.text_input(
      'Search Trader Name:',
      placeholder='Type trader name (e.g., Trader_4892)...',
  )

  display_df = filtered_df
  if search_query:
    display_df = display_df[
        display_df['Trader_Name'].str.contains(search_query, case=False, na=False)
    ]

  st.dataframe(display_df, use_container_width=True)
  st.caption(f'Showing {len(display_df)} matching records.')

with tab3:
  st.subheader('Simulate New Field Entry & M-Pesa Payment')
  st.markdown(
      'All inspection fees are strictly cashless via M-Pesa to prevent revenue'
      ' leakage and cash handling.'
  )

  # Initialize receipt state session variables if not present
  if 'last_receipt' not in st.session_state:
    st.session_state['last_receipt'] = None
  if 'last_filename' not in st.session_state:
    st.session_state['last_filename'] = None

  with st.form('inspection_form'):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
      new_trader = st.text_input('Trader / Business Name')
      new_equipment = st.selectbox(
          'Equipment Type',
          [
              'Counter Scale',
              'Platform Scale',
              'Fuel Dispenser',
              'Spring Balance',
              'Mass Piece',
          ],
      )
      phone_number = st.text_input(
          'Trader Phone Number (M-Pesa)', placeholder='0712345678'
      )
    with f_col2:
      new_subcounty = st.selectbox(
          'Sub-County',
          ['Central Ward', 'North Sub-County', 'South Market', 'East Division'],
      )
      new_status = st.selectbox(
          'Inspection Result', ['Passed', 'Rejected', 'Conditional Pass']
      )
      mpesa_code = st.text_input(
          'M-Pesa Confirmation Code', placeholder='e.g., QHC792XKL1'
      )

    submitted = st.form_submit_button('Verify Payment & Submit Digital Record')
    if submitted:
      if new_trader.strip() == '':
        st.warning('Please enter a valid Trader / Business Name.')
      elif len(mpesa_code.strip()) < 8:
        st.error(
            '⚠️ Transaction Blocked: A valid M-Pesa confirmation code is'
            ' required (Strictly No Cash Allowed).'
        )
      else:
        fee_amount = 3000 if new_status == 'Passed' else 1000
        new_row = pd.DataFrame({
            'Year': [2026],
            'Trader_Name': [new_trader],
            'Sub_County': [new_subcounty],
            'Equipment_Type': [new_equipment],
            'Inspection_Status': [new_status],
            'Fee_Collected': [fee_amount],
        })
        st.session_state['df'] = pd.concat(
            [st.session_state['df'], new_row], ignore_index=True
        )

        # Store receipt content safely in session state outside the form block
        st.session_state['last_filename'] = f'Mpesa_Receipt_{new_trader}.txt'
        st.session_state['last_receipt'] = f"""
==================================================
   COUNTY WEIGHTS & MEASURES DIGITAL REGISTRY
          OFFICIAL CASHLESS M-PESA RECEIPT
==================================================
Date / Year: 2026 Field Audit Cycle
Trader / Business: {new_trader}
Phone Contact: {phone_number}
Sub-County Region: {new_subcounty}
Equipment Verified: {new_equipment}
Inspection Status: {new_status}
--------------------------------------------------
M-PESA TRANSACTION DETAILS:
Confirmation Code: {mpesa_code.upper()}
Amount Paid: KES {fee_amount:,}
Payment Status: CONFIRMED & RECONCILED
--------------------------------------------------
Certified by: County Field Inspector Unit
Status: Logged & Verified in Master Database
==================================================
"""
        st.success(
            f'Payment of KES {fee_amount:,} verified via M-Pesa code'
            f' **{mpesa_code.upper()}** for **{new_trader}**! Record synced'
            ' to county master database.'
        )

  # --- DOWNLOAD BUTTON PLACED OUTSIDE THE FORM ---
  if st.session_state['last_receipt'] is not None:
    st.markdown('---')
    st.subheader('📥 Ready for Issuance')
    st.download_button(
        label='Download Official M-Pesa Receipt (TXT)',
        data=st.session_state['last_receipt'],
        file_name=st.session_state['last_filename'],
        mime='text/plain',
    )
