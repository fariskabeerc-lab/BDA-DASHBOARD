import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="Executive Sales Report", layout="wide", page_icon="📈")

# Professional Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; color: #1f3b4d; }
    .report-header { color: #1f3b4d; border-bottom: 2px solid #1f3b4d; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# DATA LOADING & CLEANING
# ===============================
FILE_PATH = r"TARGET STREAMLIt.xlsx"

@st.cache_data
def load_and_clean(path):
    try:
        df = pd.read_excel(path)
        df.columns = df.columns.str.strip()
        
        # Clean numeric columns (Remove commas, convert to float)
        for col in ["Total Sales", "Total Profit", "Margin (%)"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        
        # Extract Month and Category
        df["Month"] = df["MAIN"].astype(str).str.split().str[0].str.upper()
        
        def categorize(text):
            text = str(text).upper()
            if "DAILY" in text: return "IGNORE"
            if "TARGET" in text: return "TARGET"
            if "ACHIEVED" in text: return "ACHIEVED"
            return "IGNORE"
        
        df["Category"] = df["MAIN"].apply(categorize)
        return df[df["Category"] != "IGNORE"]
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

df_raw = load_and_clean(FILE_PATH)

if df_raw is not None:
    # Split into Target vs Achievement
    t_df = df_raw[df_raw["Category"] == "TARGET"].rename(columns={"Total Sales": "Target", "Total Profit": "T_Profit", "Margin (%)": "T_Margin"})
    a_df = df_raw[df_raw["Category"] == "ACHIEVED"].rename(columns={"Total Sales": "Actual", "Total Profit": "A_Profit", "Margin (%)": "A_Margin"})
    
    # Merge for Jan (since Feb/Mar actuals are 0)
    report_df = pd.merge(t_df, a_df[["OUTLET", "Month", "Actual", "A_Profit", "A_Margin"]], on=["OUTLET", "Month"], how="left").fillna(0)

    # ===============================
    # TOP HEADER
    # ===============================
    st.markdown("<h1 class='report-header'>Outlet Sales Performance Report</h1>", unsafe_allow_html=True)
    st.write(f"Reporting Period: January – March | File: {FILE_PATH.split('/')[-1]}")

    # ===============================
    # KPI SECTION (OVERALL)
    # ===============================
    jan_data = report_df[report_df["Month"] == "JAN"]
    total_jan_target = jan_data["Target"].sum()
    total_jan_actual = jan_data["Actual"].sum()
    gap = total_jan_target - total_jan_actual
    perf_pct = (total_jan_actual / total_jan_target * 100) if total_jan_target > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jan Total Target", f"{total_jan_target:,.0f}")
    c2.metric("Jan Total Achieved", f"{total_jan_actual:,.0f}")
    c3.metric("Jan Sales Gap", f"{gap:,.0f}", delta_color="inverse")
    c4.metric("Achievement Rate", f"{perf_pct:.1f}%")

    st.markdown("---")

    # ===============================
    # CHART: TARGET VS ACTUAL (BY OUTLET)
    # ===============================
    st.subheader("📊 January Performance: Target vs. Actual by Outlet")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=jan_data["OUTLET"], y=jan_data["Target"], name="Target", marker_color='#D1D5DB'))
    fig.add_trace(go.Bar(x=jan_data["OUTLET"], y=jan_data["Actual"], name="Actual", marker_color='#0056b3'))

    fig.update_layout(barmode='group', height=450, margin=dict(t=20), xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # SECTION: FEB & MAR TARGETS
    # ===============================
    st.markdown("### 📅 Upcoming Targets (Q1 Planning)")
    st.info("The following values represent the set targets for the upcoming months.")
    
    feb_mar = report_df[report_df["Month"].isin(["FEB", "MAR"])]
    
    # Pivot for clean comparison
    upcoming_pivot = feb_mar.pivot(index="OUTLET", columns="Month", values="Target").reset_index()
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.write("**Target Breakdown by Month**")
        st.dataframe(
            upcoming_pivot.style.format({"FEB": "{:,.0f}", "MAR": "{:,.0f}"}),
            use_container_width=True
        )

    with col_right:
        # Mini bar chart for Feb vs Mar totals
        fm_totals = feb_mar.groupby("Month")["Target"].sum().reindex(["FEB", "MAR"])
        fig_fm = go.Figure(data=[go.Bar(x=fm_totals.index, y=fm_totals.values, marker_color='#ffa500')])
        fig_fm.update_layout(height=250, title="Total Budget (Feb vs Mar)", margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_fm, use_container_width=True)

    # ===============================
    # FULL DATA SUMMARY
    # ===============================
    st.markdown("### 📋 Detailed Summary Table")
    
    # Add Achievement % for Jan
    jan_data["Achievement %"] = (jan_data["Actual"] / jan_data["Target"] * 100).round(1)
    
    final_table = report_df[["OUTLET", "Month", "Target", "Actual", "T_Profit"]].copy()
    
    st.dataframe(
        final_table.style.format({
            "Target": "{:,.0f}",
            "Actual": "{:,.0f}",
            "T_Profit": "{:,.0f}"
        }),
        use_container_width=True
    )

    st.markdown("---")
    st.caption("Internal Management Report - Generated for Outlet Performance Review")
