import streamlit as st
import pandas as pd
import plotly.express as px


# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Outlet Performance Dashboard",
    layout="wide",
    page_icon="📊"
)


# ===============================
# FILE PATH (EDIT HERE)
# ===============================

FILE_PATH = r"TARGET STREAMLIt.xlsx"
# 👆 Change this to your actual Excel file path


# ===============================
# CUSTOM CSS
# ===============================
st.markdown("""
<style>

h1 {
    text-align:center;
    color:#1f4e79;
}

.metric-box {
    background-color:#f8f9fa;
    padding:15px;
    border-radius:12px;
    text-align:center;
    box-shadow:0px 2px 6px rgba(0,0,0,0.1);
}

.good {color:green; font-weight:bold;}
.bad {color:red; font-weight:bold;}
.avg {color:orange; font-weight:bold;}

</style>
""", unsafe_allow_html=True)


# ===============================
# TITLE
# ===============================

st.title("📈 Outlet Sales Performance Dashboard")
st.markdown("### Management Review | Targets vs Achievement")


# ===============================
# LOAD DATA
# ===============================

try:
    df = pd.read_excel(FILE_PATH)
except:
    st.error("❌ File not found. Please check the FILE_PATH.")
    st.stop()


# ===============================
# CLEAN DATA
# ===============================

for col in ["Total Sales", "Margin (%)", "Total Profit"]:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "")
            .replace("nan", "")
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")


df = df.dropna(subset=["Total Sales"], how="all")


# ===============================
# SPLIT MONTH & TYPE
# ===============================

df[["Month", "Type"]] = df["MAIN"].str.split(" ", expand=True)


# ===============================
# FILTER TARGET & ACHIEVED
# ===============================

targets = df[df["Type"] == "TARGET"]
achieved = df[df["Type"] == "ACHIEVED"]


targets = targets.rename(columns={
    "Total Sales": "Target Sales",
    "Total Profit": "Target Profit"
})

achieved = achieved.rename(columns={
    "Total Sales": "Achieved Sales",
    "Total Profit": "Achieved Profit"
})


# ===============================
# MERGE DATA
# ===============================

summary = pd.merge(
    targets,
    achieved,
    on=["OUTLET", "Month"],
    how="left"
)


# ===============================
# CALCULATIONS
# ===============================

summary["Sales Gap"] = summary["Target Sales"] - summary["Achieved Sales"]

summary["Achievement %"] = (
    (summary["Achieved Sales"] / summary["Target Sales"]) * 100
).round(1)


def status(val):
    if val >= 95:
        return "Excellent"
    elif val >= 85:
        return "Good"
    else:
        return "Needs Improvement"


summary["Status"] = summary["Achievement %"].apply(status)


# ===============================
# SIDEBAR FILTERS
# ===============================

st.sidebar.header("🎯 Filters")


# ✅ Outlet Selector
selected_outlet = st.sidebar.selectbox(
    "Select Outlet",
    ["All Outlets"] + list(summary["OUTLET"].unique())
)


# ✅ Month Selector
selected_months = st.sidebar.multiselect(
    "Select Month",
    options=summary["Month"].unique(),
    default=summary["Month"].unique()
)


# ===============================
# APPLY FILTERS
# ===============================

filtered = summary.copy()

if selected_outlet != "All Outlets":
    filtered = filtered[filtered["OUTLET"] == selected_outlet]

filtered = filtered[
    filtered["Month"].isin(selected_months)
]


# ===============================
# KPI SECTION
# ===============================

st.markdown("## 📌 Overall Performance")

col1, col2, col3, col4 = st.columns(4)

total_target = filtered["Target Sales"].sum()
total_achieved = filtered["Achieved Sales"].sum()
total_gap = filtered["Sales Gap"].sum()
avg_ach = filtered["Achievement %"].mean()


with col1:
    st.metric("🎯 Total Target", f"{total_target:,.0f}")

with col2:
    st.metric("✅ Achieved", f"{total_achieved:,.0f}")

with col3:
    st.metric("📉 Gap", f"{total_gap:,.0f}")

with col4:
    st.metric("📊 Avg Achievement %", f"{avg_ach:.1f}%")


# ===============================
# MAIN TABLE
# ===============================

st.markdown("## 📋 Outlet Performance Summary")

display_df = filtered[[
    "OUTLET",
    "Month",
    "Target Sales",
    "Achieved Sales",
    "Sales Gap",
    "Achievement %",
    "Status"
]].copy()


def highlight(row):
    if row["Status"] == "Excellent":
        return ["background-color:#d4edda"] * len(row)
    elif row["Status"] == "Good":
        return ["background-color:#fff3cd"] * len(row)
    else:
        return ["background-color:#f8d7da"] * len(row)


st.dataframe(
    display_df
    .style
    .apply(highlight, axis=1)
    .format({
        "Target Sales": "{:,.0f}",
        "Achieved Sales": "{:,.0f}",
        "Sales Gap": "{:,.0f}",
        "Achievement %": "{:.1f}%"
    }),
    use_container_width=True
)


# ===============================
# CHART
# ===============================

st.markdown("## 📊 Target vs Achievement Comparison")


chart_df = filtered.melt(
    id_vars=["OUTLET", "Month"],
    value_vars=["Target Sales", "Achieved Sales"],
    var_name="Type",
    value_name="Sales"
)


fig = px.bar(
    chart_df,
    x="Month",
    y="Sales",
    color="Type",
    barmode="group",
    height=500,
    title="Monthly Performance Comparison"
)

st.plotly_chart(fig, use_container_width=True)


# ===============================
# FEB & MAR MOTIVATION
# ===============================

st.markdown("## 🚀 Feb & Mar Growth Opportunity")


fm = filtered[filtered["Month"].isin(["FEB", "MAR"])]


for outlet in fm["OUTLET"].unique():

    temp = fm[fm["OUTLET"] == outlet]

    if temp.empty:
        continue

    avg = temp["Achievement %"].mean()
    gap = temp["Sales Gap"].sum()

    st.markdown(f"### 🏪 {outlet}")

    if avg >= 85:
        st.success(
            f"✅ Strong Performance ({avg:.1f}%) — "
            "Feb & Mar targets are highly achievable."
        )
    else:
        st.warning(
            f"⚠️ Achievement: {avg:.1f}% | "
            f"Gap: {gap:,.0f}. Strong push can close this."
        )


# ===============================
# INSIGHTS
# ===============================

st.markdown("## 💡 Management Insights")


best = filtered.sort_values("Achievement %", ascending=False).head(3)
worst = filtered.sort_values("Achievement %").head(3)


col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌟 Top Performers")
    st.dataframe(best[["OUTLET", "Month", "Achievement %"]])

with col2:
    st.markdown("### ⚠️ Focus Areas")
    st.dataframe(worst[["OUTLET", "Month", "Achievement %"]])


# ===============================
# FOOTER
# ===============================

st.markdown("---")
st.markdown("📊 Prepared for Management Review | Performance Analytics System")
