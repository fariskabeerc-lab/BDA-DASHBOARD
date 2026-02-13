import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Executive Rebate Dashboard", layout="wide")

# Custom CSS for a cleaner "Enterprise" look
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { border: 1px solid #d1d5db; padding: 10px; border-radius: 10px; background: white; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================
# DATA LOADING
# ==============================
FILE_PATH = r"BDA STREAMLIT.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()
    # Ensure all numerical columns are cleaned
    num_cols = ['2026 TOTEL PURCHASE', 'BASE TARGET', '2025 TOTEL PURCHASE', 'SALE OF 2025',
                'SLAB A', 'SLAB B', 'SLAB C', 'SLAB D', 'SLAB E', 
                'SLAB A ACHIEVE PAYABLE AMOUNT%', 'SLAB B ACHIEVE PAYABLE AMOUNT%',
                'SLAB C ACHIEVE PAYABLE AMOUNT%', 'SLAB D ACHIEVE PAYABLE AMOUNT%',
                'SLAB E ACHIEVE PAYABLE AMOUNT%']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("📊 Filter View")
supplier_list = sorted(df["supplier"].unique().tolist())
selected_supplier = st.sidebar.selectbox("Choose Supplier", supplier_list)

# Filter for the specific supplier
s_df = df[df["supplier"] == selected_supplier].copy()

# ==============================
# AGGREGATED CALCULATIONS
# ==============================
p_2026 = s_df["2026 TOTEL PURCHASE"].sum()
p_2025 = s_df["2025 TOTEL PURCHASE"].sum()
s_2025 = s_df["SALE OF 2025"].sum()
b_target = s_df["BASE TARGET"].sum()

# Slab Logic - Using the first row of the supplier data for slab definitions
row = s_df.iloc[0]
slabs_config = [
    ('SLAB A', 'SLAB A ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB B', 'SLAB B ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB C', 'SLAB C ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB D', 'SLAB D ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB E', 'SLAB E ACHIEVE PAYABLE AMOUNT%')
]

active_slabs = []
earned_pct = 0
for s_col, p_col in slabs_config:
    target_val = row[s_col]
    if target_val > 0:
        is_achieved = p_2026 >= target_val
        gap = max(0, target_val - p_2026)
        active_slabs.append({
            "Slab": s_col,
            "Target": target_val,
            "Gap": gap,
            "Percent": row[p_col],
            "Status": "Achieved" if is_achieved else "Pending"
        })
        if is_achieved:
            earned_pct = row[p_col]

est_rebate = p_2026 * (earned_pct / 100)

# ==============================
# DASHBOARD UI START
# ==============================
st.title(f"🏆 {selected_supplier} Performance")
st.markdown("---")

# KPI BOXES
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("2026 Purchase", f"{p_2026:,.0f}")
kpi2.metric("Target Gap", f"{max(0, b_target - p_2026):,.0f}", delta_color="inverse")
kpi3.metric("Current Rebate %", f"{earned_pct}%")
kpi4.metric("Est. Rebate Value", f"{est_rebate:,.0f}")

st.markdown("### 📈 Achievement Roadmap")

col_left, col_right = st.columns([1, 1])

with col_left:
    # 1. GAUGE CHART (WHERE ARE WE VS TARGET)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = p_2026,
        title = {'text': "Progress vs Base Target"},
        gauge = {
            'axis': {'range': [0, max(b_target, p_2026) * 1.2]},
            'bar': {'color': "#1f77b4"},
            'steps': [{'range': [0, b_target], 'color': "#ffe4e4"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'value': b_target}
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_right:
    # 2. COMPARISON BAR (2025 vs 2026 vs Target)
    comp_df = pd.DataFrame({
        'Metric': ['2025 Sales', '2025 Purchase', 'Base Target', '2026 Purchase'],
        'Value': [s_2025, p_2025, b_target, p_2026]
    })
    fig_bar = px.bar(comp_df, x='Metric', y='Value', color='Metric', 
                     text_auto='.3s', title="Historical vs Target Comparison")
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# ==============================
# SLAB PROGRESS (REMAINING TO BUY)
# ==============================
st.markdown("### 🪜 How much more to buy for Slabs?")
if active_slabs:
    slab_df = pd.DataFrame(active_slabs)
    
    # Create a "Bridge" chart or stacked chart showing current vs gap
    fig_slab_prog = go.Figure()
    fig_slab_prog.add_trace(go.Bar(name='Already Purchased', x=slab_df['Slab'], y=[p_2026]*len(slab_df), marker_color='#2ecc71'))
    fig_slab_prog.add_trace(go.Bar(name='Remaining Gap', x=slab_df['Slab'], y=slab_df['Gap'], marker_color='#e74c3c'))
    
    fig_slab_prog.update_layout(barmode='stack', title="Current Purchase + Needed for each Slab Level")
    st.plotly_chart(fig_slab_prog, use_container_width=True)
else:
    st.info("No active slabs found for this supplier.")

# ==============================
# BRAND & CATEGORY SUMMARY
# ==============================
st.divider()
st.markdown("### 📦 Brand & Category Breakdown")
c_brand, c_cat = st.columns(2)

with c_brand:
    brand_data = s_df.groupby("BRAND")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_brand = px.pie(brand_data, names='BRAND', values='2026 TOTEL PURCHASE', 
                       hole=0.4, title="Purchase by Brand")
    st.plotly_chart(fig_brand, use_container_width=True)

with c_cat:
    cat_data = s_df.groupby("CATEGORY")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_cat = px.bar(cat_data, x='CATEGORY', y='2026 TOTEL PURCHASE', 
                     color='CATEGORY', title="Purchase by Category")
    st.plotly_chart(fig_cat, use_container_width=True)

# ==============================
# KEY INSIGHTS
# ==============================
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Key Insights")
st.sidebar.write(f"**Achieved:** {earned_pct}% Rebate Tier")
if b_target > p_2026:
    st.sidebar.error(f"Need **{b_target - p_2026:,.0f}** to reach Base Target.")
else:
    st.sidebar.success("✅ Base Target Achieved!")

st.success("Analysis Complete")
