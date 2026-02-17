import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ===============================
# PAGE CONFIG & STYLING
# ===============================
st.set_page_config(page_title="Executive Performance Dashboard", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #1f3b4d; }
    .header-style { font-size: 30px; font-weight: bold; color: #1f3b4d; border-bottom: 3px solid #0056b3; }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# DATA LOADING & CLEANING
# ===============================
FILE_PATH = r"TARGET STREAMLIt.xlsx"

@st.cache_data
def load_and_process(path):
    try:
        df = pd.read_excel(path)
        df.columns = df.columns.str.strip()
        
        # Clean Numeric Columns
        for col in ["Total Sales", "Total Profit", "Margin (%)"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        
        # Extract Month & Type
        df["Month"] = df["MAIN"].astype(str).str.split().str[0].str.upper()
        df["Type"] = df["MAIN"].apply(lambda x: "TARGET" if "TARGET" in str(x).upper() and "DAILY" not in str(x).upper() 
                                     else ("ACHIEVED" if "ACHIEVED" in str(x).upper() and "DAILY" not in str(x).upper() else "IGNORE"))
        
        df = df[df["Type"] != "IGNORE"]
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df_raw = load_and_process(FILE_PATH)

if df_raw is not None:
    # --- Sidebar Filters ---
    st.sidebar.header("🎯 Navigation")
    outlets = sorted(df_raw["OUTLET"].unique())
    selected_outlet = st.sidebar.selectbox("Select Outlet", outlets)

    # --- Data Processing for Selected Outlet ---
    outlet_df = df_raw[df_raw["OUTLET"] == selected_outlet]
    
    # Pivot Data
    pivot = outlet_df.pivot(index="Month", columns="Type", values=["Total Sales", "Total Profit", "Margin (%)"])
    pivot.columns = [f"{col}_{type}" for col, type in pivot.columns]
    pivot = pivot.fillna(0).reset_index()

    # Define Order
    pivot['Month'] = pd.Categorical(pivot['Month'], categories=['JAN', 'FEB', 'MAR'], ordered=True)
    pivot = pivot.sort_values('Month')

    # ===============================
    # HEADER SECTION
    # ===============================
    st.markdown(f"<p class='header-style'>📊 Performance Review: {selected_outlet}</p>", unsafe_allow_html=True)
    
    # JAN ONLY KPIs
    jan = pivot[pivot["Month"] == "JAN"].iloc[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jan Target", f"{jan['Total Sales_TARGET']:,.0f}")
    c2.metric("Jan Achieved", f"{jan['Total Sales_ACHIEVED']:,.0f}")
    c3.metric("Jan GP %", f"{jan['Margin (%)_ACHIEVED']:.1f}%")
    c4.metric("Jan Profit", f"{jan['Total Profit_ACHIEVED']:,.0f}")

    st.markdown("---")

    # ===============================
    # ROW 1: SALES & PROFIT GRAPHS (JANUARY)
    # ===============================
    st.subheader("📈 January Performance Analysis")
    col_left, col_right = st.columns(2)

    with col_left:
        # Sales vs Target Chart
        fig_sales = go.Figure()
        fig_sales.add_trace(go.Bar(name="Target", x=["January"], y=[jan["Total Sales_TARGET"]], marker_color='#D1D5DB'))
        fig_sales.add_trace(go.Bar(name="Actual", x=["January"], y=[jan["Total Sales_ACHIEVED"]], marker_color='#0056b3'))
        fig_sales.update_layout(title="Sales vs Target", barmode='group', height=400, showlegend=True)
        st.plotly_chart(fig_sales, use_container_width=True)

    with col_right:
        # Profit vs Target Chart
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Bar(name="Target Profit", x=["January"], y=[jan["Total Profit_TARGET"]], marker_color='#E5E7E9'))
        fig_profit.add_trace(go.Bar(name="Actual Profit", x=["January"], y=[jan["Total Profit_ACHIEVED"]], marker_color='#28a745'))
        fig_profit.update_layout(title="Profit vs Target", barmode='group', height=400)
        st.plotly_chart(fig_profit, use_container_width=True)

    # ===============================
    # ROW 2: GP% COMPARISON
    # ===============================
    st.subheader("💎 Margin (GP%) Comparison")
    
    fig_gp = go.Figure()
    fig_gp.add_trace(go.Scatter(x=["January"], y=[jan["Margin (%)_TARGET"]], name="Target GP%", mode='lines+markers', line=dict(color='red', dash='dash')))
    fig_gp.add_trace(go.Bar(x=["January"], y=[jan["Margin (%)_ACHIEVED"]], name="Actual GP%", marker_color='#FF8C00', width=0.3))
    fig_gp.update_layout(title="GP% Performance", height=350, yaxis_title="Percentage (%)")
    st.plotly_chart(fig_gp, use_container_width=True)

    # ===============================
    # ROW 3: FUTURE TARGETS (FEB & MAR)
    # ===============================
    st.markdown("---")
    st.subheader("📅 Q1 Forward Planning: Feb & Mar Targets")
    
    fm_data = pivot[pivot["Month"].isin(["FEB", "MAR"])]
    
    col_f, col_m = st.columns(2)
    
    for i, month in enumerate(["FEB", "MAR"]):
        m_row = fm_data[fm_data["Month"] == month].iloc[0]
        with (col_f if i == 0 else col_m):
            st.markdown(f"#### {month} Forecast")
            st.write(f"**Target Sales:** {m_row['Total Sales_TARGET']:,.0f}")
            st.write(f"**Expected Profit:** {m_row['Total Profit_TARGET']:,.0f}")
            st.write(f"**Target Margin:** {m_row['Margin (%)_TARGET']:.1f}%")
            
            # Mini Visual for Target
            st.progress(0.0) # Visual placeholder since actual is 0
            st.caption(f"Waiting for {month} actual data...")

    # ===============================
    # DATA TABLE
    # ===============================
    st.markdown("### 📋 Full Data Breakdown")
    st.dataframe(
        pivot[["Month", "Total Sales_TARGET", "Total Sales_ACHIEVED", "Total Profit_TARGET", "Total Profit_ACHIEVED", "Margin (%)_TARGET", "Margin (%)_ACHIEVED"]]
        .style.format({
            "Total Sales_TARGET": "{:,.0f}", "Total Sales_ACHIEVED": "{:,.0f}",
            "Total Profit_TARGET": "{:,.0f}", "Total Profit_ACHIEVED": "{:,.0f}",
            "Margin (%)_TARGET": "{:.1f}%", "Margin (%)_ACHIEVED": "{:.1f}%"
        }),
        use_container_width=True
    )
