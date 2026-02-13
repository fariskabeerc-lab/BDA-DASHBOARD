import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# PAGE CONFIG & STYLING
# ==============================
st.set_page_config(page_title="Strategic Rebate Analyzer", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    [data-testid="stMetricValue"] { color: #1f77b4; }
    .main { background-color: #f0f2f6; }
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
    # Convert all possible numeric columns and handle NaNs
    num_cols = ['2026 TOTEL PURCHASE', 'BASE TARGET', '2025 TOTEL PURCHASE', 'SALE OF 2025',
                'SLAB A', 'SLAB B', 'SLAB C', 'SLAB D', 'SLAB E']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# ==============================
# SIDEBAR & FILTERS
# ==============================
st.sidebar.header("🎯 Dashboard Controls")
supplier_list = sorted(df["supplier"].unique().tolist())
selected_supplier = st.sidebar.selectbox("Select a Supplier to Deep-Dive", supplier_list)

# Filter data for the selected supplier
s_data = df[df["supplier"] == selected_supplier].copy()

# ==============================
# CALCULATIONS
# ==============================
p_2026 = s_data["2026 TOTEL PURCHASE"].sum()
p_2025 = s_data["2025 TOTEL PURCHASE"].sum()
s_2025 = s_data["SALE OF 2025"].sum()
b_target = s_data["BASE TARGET"].sum()

# Identify active slabs (ignoring 0)
slabs_ref = [('SLAB A', 'SLAB A ACHIEVE PAYABLE AMOUNT%'), 
             ('SLAB B', 'SLAB B ACHIEVE PAYABLE AMOUNT%'),
             ('SLAB C', 'SLAB C ACHIEVE PAYABLE AMOUNT%'),
             ('SLAB D', 'SLAB D ACHIEVE PAYABLE AMOUNT%'),
             ('SLAB E', 'SLAB E ACHIEVE PAYABLE AMOUNT%')]

active_slabs = []
current_rebate_pct = 0
for s_name, p_name in slabs_ref:
    val = s_data[s_name].iloc[0]
    pct = s_data[p_name].iloc[0]
    if val > 0:
        gap = max(0, val - p_2026)
        achieved = p_2026 >= val
        active_slabs.append({"Slab": s_name, "Target": val, "Gap": gap, "Pct": pct, "Status": achieved})
        if achieved:
            current_rebate_pct = pct

est_rebate_val = p_2026 * (current_rebate_pct / 100)

# ==============================
# HEADER SECTION
# ==============================
st.title(f"🏢 {selected_supplier} Performance Dashboard")
st.markdown(f"**Current Status:** {'Target Achieved ✅' if p_2026 >= b_target else 'Below Base Target ⚠️'}")

# Top Row Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("2026 Purchase", f"{p_2026:,.0f}")
c2.metric("Base Target", f"{b_target:,.0f}", f"{p_2026 - b_target:,.0f}")
c3.metric("Current Rebate %", f"{current_rebate_pct}%")
c4.metric("Est. Rebate Value", f"{est_rebate_val:,.0f}")

st.divider()

# ==============================
# VISUALS: PIE/GAUGE & BARS
# ==============================
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📍 Target Achievement Status")
    # Gauge chart for Base Target
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = p_2026,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Purchase vs Base Target", 'font': {'size': 18}},
        delta = {'reference': b_target, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [0, max(b_target, p_2026) * 1.2]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, b_target], 'color': "#ffcccc"},
                {'range': [b_target, max(b_target, p_2026) * 1.2], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': b_target
            }
        }
    ))
    fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_right:
    st.subheader("📊 Comparative Performance (History vs Target)")
    # Comprehensive bar chart
    bar_data = {
        'Category': ['2025 Sales', '2025 Purchase', 'Base Target', '2026 Purchase'],
        'Amount': [s_2025, p_2025, b_target, p_2026],
        'Color': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
    }
    fig_bar = px.bar(bar_data, x='Category', y='Amount', color='Category', 
                     text_auto='.3s', color_discrete_map="identity")
    fig_bar.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# ==============================
# SLAB PROGRESSION (THE "BUY" GRAPH)
# ==============================
st.subheader("🪜 Slab Progression: How much more to buy?")
if active_slabs:
    slab_df = pd.DataFrame(active_slabs)
    
    # Custom Bar for Slab Targets vs Current
    fig_slabs = go.Figure()
    fig_slabs.add_trace(go.Bar(name='Current Purchase', x=slab_df['Slab'], y=[p_2026]*len(slab_df), marker_color='#1f77b4'))
    fig_slabs.add_trace(go.Bar(name='Gap to Achieve', x=slab_df['Slab'], y=slab_df['Gap'], marker_color='#ff7f0e'))
    
    fig_slabs.update_layout(barmode='stack', title="Current Purchase + Amount Needed per Slab", height=400)
    st.plotly_chart(fig_slabs, use_container_width=True)
    
    # Detailed Info Cards for Slabs
    slab_cols = st.columns(len(active_slabs))
    for i, s in enumerate(active_slabs):
        with slab_cols[i]:
            color = "green" if s['Status'] else "red"
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding:10px; border-radius:5px; text-align:center;">
                <h4 style="margin:0;">{s['Slab']}</h4>
                <p style="color:{color}; font-weight:bold; margin:0;">{s['Pct']}% Rebate</p>
                <small>Need: {s['Gap']:,.0f}</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No progressive slabs defined for this supplier.")

st.divider()

# ==============================
# SUMMARY: BRAND & CATEGORY
# ==============================
st.subheader("📋 Product Summary (Brand & Category)")
summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.write("**Purchase by Brand**")
    brand_summ = s_data.groupby("BRAND")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_brand = px.pie(brand_summ, names='BRAND', values='2026 TOTEL PURCHASE', hole=0.5)
    st.plotly_chart(fig_brand, use_container_width=True)

with summary_col2:
    st.write("**Purchase by Category**")
    cat_summ = s_data.groupby("CATEGORY")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_cat = px.bar(cat_summ, x='CATEGORY', y='2026 TOTEL PURCHASE', color='CATEGORY')
    st.plotly_chart(fig_cat, use_container_width=True)

# Detailed Data View
with st.expander("🔍 View Raw Supplier Breakdown"):
    st.table(s_data[['BRAND', 'CATEGORY', '2026 TOTEL PURCHASE', 'BASE TARGET']])

st.success(f"Strategy view for {selected_supplier} generated successfully.")
