import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Executive Supplier Rebate Tracker",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for a modern look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #007bff; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================
# FILE PATH & LOADING
# ==============================
FILE_PATH = r"BDA STREAMLIT.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(FILE_PATH)
        df.columns = df.columns.str.strip()
        # Clean numeric columns
        cols_to_fix = ['2026 TOTEL PURCHASE', 'BASE TARGET', '2025 TOTEL PURCHASE', 
                       'SLAB A', 'SLAB B', 'SLAB C', 'SLAB D', 'SLAB E']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

df = load_data()

# ==============================
# LOGIC: REBATE & SLAB PROCESSING
# ==============================
def process_slabs(row):
    purchase = row['2026 TOTEL PURCHASE']
    slabs = [
        ('SLAB A', 'SLAB A ACHIEVE PAYABLE AMOUNT%'),
        ('SLAB B', 'SLAB B ACHIEVE PAYABLE AMOUNT%'),
        ('SLAB C', 'SLAB C ACHIEVE PAYABLE AMOUNT%'),
        ('SLAB D', 'SLAB D ACHIEVE PAYABLE AMOUNT%'),
        ('SLAB E', 'SLAB E ACHIEVE PAYABLE AMOUNT%'),
    ]
    
    active_slabs = []
    earned_rebate = 0
    current_pct = 0
    
    for slab_col, pct_col in slabs:
        target_val = row[slab_col]
        if target_val > 0: # Ignore zero slabs
            is_achieved = purchase >= target_val
            needed = max(0, target_val - purchase)
            rebate_val = purchase * (row[pct_col] / 100) if is_achieved else 0
            
            if is_achieved:
                earned_rebate = rebate_val # Progressive: highest achieved slab wins
                current_pct = row[pct_col]

            active_slabs.append({
                "Slab": slab_col,
                "Target": target_val,
                "Needed": needed,
                "Status": "Achieved" if is_achieved else "Pending",
                "Rebate%": row[pct_col],
                "Potential Value": rebate_val
            })
            
    return active_slabs, earned_rebate, current_pct

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.title("🏢 Supplier Control")
supplier_list = ["All Suppliers"] + sorted(df["supplier"].unique().tolist())
selected_supplier = st.sidebar.selectbox("Choose Supplier", supplier_list)

# Filter Data
if selected_supplier == "All Suppliers":
    filtered_df = df
else:
    filtered_df = df[df["supplier"] == selected_supplier]

# ==============================
# CALCULATIONS (TOTALS)
# ==============================
total_purchase_2026 = filtered_df["2026 TOTEL PURCHASE"].sum()
total_purchase_2025 = filtered_df["2025 TOTEL PURCHASE"].sum()
total_base_target = filtered_df["BASE TARGET"].sum()
total_gap_to_base = max(0, total_base_target - total_purchase_2026)

# Calculate dynamic rebates for the group
total_est_rebate = 0
all_slab_records = []

for _, row in filtered_df.iterrows():
    slabs_list, rebate, _ = process_slabs(row)
    total_est_rebate += rebate
    for s in slabs_list:
        s['Supplier'] = row['supplier']
        all_slab_records.append(s)

slab_summary_df = pd.DataFrame(all_slab_records)

# ==============================
# MAIN DASHBOARD UI
# ==============================
st.title("📊 Supplier Progressive Rebate Dashboard")
st.markdown(f"**Viewing:** {selected_supplier}")

# --- TOP KPI ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("2026 Total Purchase", f"{total_purchase_2026:,.0f}")
m2.metric("Base Target Gap", f"{total_gap_to_base:,.0f}", delta_color="inverse")
m3.metric("Estimated Rebate", f"{total_est_rebate:,.0f}")
m4.metric("2025 Total Sales", f"{total_purchase_2025:,.0f}")

st.divider()

# --- GRAPHS SECTION ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🎯 Target vs. Actual Comparison")
    comp_data = pd.DataFrame({
        'Category': ['2025 Purchase', '2026 Purchase', 'Base Target'],
        'Amount': [total_purchase_2025, total_purchase_2026, total_base_target]
    })
    fig_comp = px.bar(comp_data, x='Category', y='Amount', color='Category',
                     text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_comp, use_container_width=True)

with col_right:
    st.subheader("🥧 2026 Purchase Distribution")
    fig_pie = px.pie(filtered_df, values='2026 TOTEL PURCHASE', names='supplier', 
                    hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- SLAB ANALYSIS (Interactive Bar Chart) ---
st.subheader("🪜 Progressive Slab Progress (Amount Needed to Reach Next Level)")
if not slab_summary_df.empty:
    # Filter only pending slabs to show what needs to be bought
    pending_slabs = slab_summary_df[slab_summary_df["Status"] == "Pending"]
    
    if not pending_slabs.empty:
        fig_slabs = px.bar(
            pending_slabs, 
            x="Slab", 
            y="Needed", 
            color="Supplier",
            title="Purchase Required per Slab Level",
            barmode="group",
            text="Needed"
        )
        fig_slabs.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        st.plotly_chart(fig_slabs, use_container_width=True)
    else:
        st.success("🔥 All Slabs have been achieved for the selected criteria!")

# --- DETAILED DATA TABLE ---
with st.expander("📝 View Detailed Slab Breakdown"):
    st.dataframe(slab_summary_df, use_container_width=True)

# --- KEY INSIGHTS SECTION ---
st.divider()
st.subheader("💡 Strategic Key Insights")
c1, c2 = st.columns(2)

with c1:
    st.info(f"**Rebate Status:** You are currently on track to receive **{total_est_rebate:,.2f}** in total rebates.")
    if total_gap_to_base > 0:
        st.warning(f"**Base Target Alert:** You need to purchase **{total_gap_to_base:,.2f}** more to hit the Base Target.")
    else:
        st.success("**Target Met:** Base targets have been exceeded!")

with c2:
    achieved_count = len(slab_summary_df[slab_summary_df["Status"] == "Achieved"])
    total_active_slabs = len(slab_summary_df)
    st.write(f"✅ **Slabs Achieved:** {achieved_count} of {total_active_slabs}")
    
    if selected_supplier != "All Suppliers":
        # Specific logic for single supplier
        row = filtered_df.iloc[0]
        growth = ((total_purchase_2026 - total_purchase_2025) / total_purchase_2025 * 100) if total_purchase_2025 > 0 else 0
        st.write(f"📈 **Year-over-Year Growth:** {growth:.1f}%")

st.success("Dashboard Updated Successfully ✅")
