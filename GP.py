import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# 1. PAGE CONFIG & ENHANCED STYLING
# ==============================
st.set_page_config(
    page_title="Al Madina Group - Supplier Rebate Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for Dark Metric Values and Clean Interface
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    /* FORCING KEY INSIGHT VALUES TO BE DARK */
    [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }

    /* Label Styling */
    [data-testid="stMetricLabel"] {
        color: #4b5563 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================
# 2. DATA LOADING & CLEANING
# ==============================
FILE_PATH = r"BDA STREAMLIT.xlsx"

@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_excel(FILE_PATH)
        df.columns = df.columns.str.strip()
        
        # Ensure critical columns are numeric for calculations
        num_cols = [
            '2026 TOTEL PURCHASE', 'BASE TARGET', '2025 TOTEL PURCHASE', 'SALE OF 2025',
            'SLAB A', 'SLAB B', 'SLAB C', 'SLAB D', 'SLAB E',
            'SLAB A ACHIEVE PAYABLE AMOUNT%', 'SLAB B ACHIEVE PAYABLE AMOUNT%',
            'SLAB C ACHIEVE PAYABLE AMOUNT%', 'SLAB D ACHIEVE PAYABLE AMOUNT%',
            'SLAB E ACHIEVE PAYABLE AMOUNT%'
        ]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading Excel: {e}")
        return pd.DataFrame()

df = load_and_clean_data()

# ==============================
# 3. SIDEBAR NAVIGATION (AL MADINA GROUP BRANDING)
# ==============================
st.sidebar.markdown("## 🏢 Al Madina Group")
st.sidebar.markdown("---")
st.sidebar.title("Supplier Filter")

supplier_list = sorted(df["supplier"].unique().tolist())
selected_supplier = st.sidebar.selectbox("Select Supplier Account", supplier_list)

st.sidebar.markdown("---")

# Filter Dataset
s_df = df[df["supplier"] == selected_supplier].copy()

# ==============================
# 4. BUSINESS LOGIC & ORDERED SLABS
# ==============================
p_2026 = s_df["2026 TOTEL PURCHASE"].sum()
p_2025 = s_df["2025 TOTEL PURCHASE"].sum()
s_2025 = s_df["SALE OF 2025"].sum()
b_target = s_df["BASE TARGET"].sum()

row = s_df.iloc[0]
slabs_ref = [
    ('SLAB A', 'SLAB A ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB B', 'SLAB B ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB C', 'SLAB C ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB D', 'SLAB D ACHIEVE PAYABLE AMOUNT%'),
    ('SLAB E', 'SLAB E ACHIEVE PAYABLE AMOUNT%')
]

active_slabs = []
current_earned_pct = 0

# FORCE ORDER: A → B → C → D → E for Left-to-Right layout
ordered_slabs = ['SLAB A', 'SLAB B', 'SLAB C', 'SLAB D', 'SLAB E']

for slab_name in ordered_slabs:
    for s_col, p_col in slabs_ref:
        if slab_name == s_col:
            t_val = row[s_col]
            if t_val > 0:
                gap = max(0, t_val - p_2026)
                is_achieved = p_2026 >= t_val
                
                active_slabs.append({
                    "Name": s_col,
                    "Target": t_val,
                    "Gap": gap,
                    "Percent": row[p_col],
                    "Status": is_achieved
                })
                # Progressive logic: highest achieved slab sets the rate
                if is_achieved:
                    current_earned_pct = row[p_col]

est_rebate_val = p_2026 * (current_earned_pct / 100)

# ==============================
# 5. HEADER & KPI CARDS (DARK VALUES)
# ==============================
st.title(f"📊 {selected_supplier} Performance Analysis")
st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
m1.metric("2026 Total Purchase", f"{p_2026:,.0f}")
m2.metric("Base Target Gap", f"{max(0, b_target - p_2026):,.0f}")
m3.metric("Earned Rebate %", f"{current_earned_pct}%")
m4.metric("Est. Rebate Value", f"{est_rebate_val:,.0f}")

st.divider()

# ==============================
# 6. ORDERED VERTICAL SLAB GRAPHS (LEFT TO RIGHT)
# ==============================
st.subheader("🪜 Individual Slab Progress (Vertical Order)")

if active_slabs:
    # Gap set to large for better visual separation
    slab_cols = st.columns(len(active_slabs), gap="large")
    
    for i, s in enumerate(active_slabs):
        with slab_cols[i]:
            fig_s = go.Figure()
            
            # Grey background bar representing the Target
            fig_s.add_trace(go.Bar(
                x=[s['Name']], y=[s['Target']],
                marker_color='#e5e7eb', hoverinfo='skip', showlegend=False
            ))
            
            # Progress bar showing actual purchase progress
            progress = min(p_2026, s['Target'])
            fig_s.add_trace(go.Bar(
                x=[s['Name']], y=[progress],
                marker_color='#10b981' if s['Status'] else '#3b82f6',
                text=f"{(progress/s['Target']*100):.1f}%",
                textposition='inside', showlegend=False
            ))
            
            fig_s.update_layout(
                barmode='overlay', height=450,
                title=f"<b>{s['Name']}</b><br>{s['Percent']}% Tier",
                title_x=0.5,
                yaxis=dict(range=[0, s['Target'] * 1.1], gridcolor='#f3f4f6'),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_s, use_container_width=True)
            
            # Actionable Gap labels
            if s['Gap'] > 0:
                st.error(f"Need: **{s['Gap']:,.0f}**")
            else:
                st.success("Slab Achieved!")
else:
    st.info("No progressive slabs found for this supplier.")

# ==============================
# 7. PRODUCT SUMMARY (BRAND & CATEGORY)
# ==============================
st.divider()
st.subheader("📋 Product & Category Breakdown")
col_pie, col_bar = st.columns(2)

with col_pie:
    brand_df = s_df.groupby("BRAND")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_brand = px.pie(brand_df, names='BRAND', values='2026 TOTEL PURCHASE', hole=0.5, title="Share by Brand")
    st.plotly_chart(fig_brand, use_container_width=True)

with col_bar:
    cat_df = s_df.groupby("CATEGORY")["2026 TOTEL PURCHASE"].sum().reset_index()
    fig_cat = px.bar(cat_df, x='CATEGORY', y='2026 TOTEL PURCHASE', title="Volume by Category", color='CATEGORY')
    st.plotly_chart(fig_cat, use_container_width=True)

# Detailed data expander for transparency
with st.expander("📂 View Detailed Data Breakdown"):
    st.dataframe(s_df[['BRAND', 'CATEGORY', '2026 TOTEL PURCHASE', 'BASE TARGET']], use_container_width=True)

st.sidebar.success("Al Madina Dashboard Ready ✅")
