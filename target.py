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
# FILE PATH (CHANGE THIS)
# ===============================

FILE_PATH = r"TARGET STREAMLIt.xlsx"
# 👆 CHANGE THIS TO YOUR FILE PATH


# ===============================
# TITLE
# ===============================

st.title("📈 Outlet Sales Performance Dashboard")
st.markdown("Review | Targets vs Achievement")


# ===============================
# LOAD FILE
# ===============================

try:
    df = pd.read_excel(FILE_PATH)
except:
    st.error("❌ File not found. Check FILE_PATH.")
    st.stop()


# ===============================
# CLEAN COLUMN NAMES
# ===============================

df.columns = df.columns.str.strip()


# ===============================
# CHECK REQUIRED COLUMNS
# ===============================

required_cols = ["OUTLET", "MAIN", "Total Sales", "Total Profit"]

missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"❌ Missing columns: {missing}")
    st.write("Found columns:", df.columns.tolist())
    st.stop()


# ===============================
# CLEAN NUMBERS
# ===============================

for col in ["Total Sales", "Total Profit"]:

    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace(["nan", "None", ""], None)
    )

    df[col] = pd.to_numeric(df[col], errors="coerce")


df = df.dropna(subset=["Total Sales"], how="all")


# ===============================
# EXTRACT MONTH
# ===============================

df["Month"] = df["MAIN"].astype(str).str.split().str[0]


# ===============================
# EXTRACT TYPE
# ===============================

def detect_type(text):

    text = str(text).upper()

    if "TARGET" in text and "DAILY" not in text:
        return "TARGET"

    if "ACHIEVED" in text and "DAILY" not in text:
        return "ACHIEVED"

    return "IGNORE"


df["Type"] = df["MAIN"].apply(detect_type)


# ===============================
# REMOVE DAILY ROWS
# ===============================

df = df[df["Type"].isin(["TARGET", "ACHIEVED"])]


# ===============================
# SPLIT TARGET / ACHIEVED
# ===============================

targets = df[df["Type"] == "TARGET"].copy()
achieved = df[df["Type"] == "ACHIEVED"].copy()


# ===============================
# RENAME COLUMNS
# ===============================

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
# BASE CALCULATIONS
# ===============================

summary["Achieved Sales"] = summary["Achieved Sales"].fillna(0)

summary["Sales Gap"] = summary["Target Sales"] - summary["Achieved Sales"]

summary["Achievement %"] = (
    summary["Achieved Sales"] / summary["Target Sales"] * 100
).round(1)

summary["Achievement %"] = summary["Achievement %"].fillna(0)


# ===============================
# AUTO-FILL FEB & MAR USING JAN
# ===============================

jan_perf = summary[summary["Month"] == "JAN"][[
    "OUTLET", "Achievement %"
]].copy()

jan_perf = jan_perf.rename(columns={
    "Achievement %": "Jan %"
})


summary = pd.merge(
    summary,
    jan_perf,
    on="OUTLET",
    how="left"
)


for i, row in summary.iterrows():

    if row["Month"] in ["FEB", "MAR"]:

        if pd.isna(row["Achieved Sales"]) or row["Achieved Sales"] == 0:

            jan_pct = row["Jan %"] / 100

            if not pd.isna(jan_pct) and jan_pct > 0:

                expected = row["Target Sales"] * jan_pct

                summary.at[i, "Achieved Sales"] = expected


# Recalculate
summary["Sales Gap"] = summary["Target Sales"] - summary["Achieved Sales"]

summary["Achievement %"] = (
    summary["Achieved Sales"] / summary["Target Sales"] * 100
).round(1)

summary["Achievement %"] = summary["Achievement %"].fillna(0)


summary = summary.drop(columns=["Jan %"])


# ===============================
# STATUS
# ===============================

def get_status(val):

    if val >= 95:
        return "Excellent"

    elif val >= 85:
        return "Good"

    else:
        return "Needs Improvement"


summary["Status"] = summary["Achievement %"].apply(get_status)


# ===============================
# SIDEBAR FILTERS
# ===============================

st.sidebar.header("🎯 Filters")


selected_outlet = st.sidebar.selectbox(
    "Select Outlet",
    ["All Outlets"] + list(summary["OUTLET"].unique())
)


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


filtered = filtered[filtered["Month"].isin(selected_months)]


# ===============================
# KPI SECTION
# ===============================

st.markdown("## 📌 Overall Performance")


c1, c2, c3, c4 = st.columns(4)


c1.metric("🎯 Target", f"{filtered['Target Sales'].sum():,.0f}")
c2.metric("✅ Achieved", f"{filtered['Achieved Sales'].sum():,.0f}")
c3.metric("📉 Gap", f"{filtered['Sales Gap'].sum():,.0f}")
c4.metric("📊 Avg %", f"{filtered['Achievement %'].mean():.1f}%")


# ===============================
# MAIN TABLE
# ===============================

st.markdown("## 📋 Outlet Performance Summary")


display = filtered[[
    "OUTLET",
    "Month",
    "Target Sales",
    "Achieved Sales",
    "Sales Gap",
    "Achievement %",
    "Status"
]]


def highlight(row):

    if row["Status"] == "Excellent":
        return ["background-color:#d4edda"] * len(row)

    if row["Status"] == "Good":
        return ["background-color:#fff3cd"] * len(row)

    return ["background-color:#f8d7da"] * len(row)


st.dataframe(
    display
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
# BAR CHART
# ===============================

st.markdown("## 📊 Target vs Achievement")


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
    height=500
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
            f"✅ Strong Performance ({avg:.1f}%) — Targets are achievable."
        )

    else:

        st.warning(
            f"⚠️ Achievement: {avg:.1f}% | Gap: {gap:,.0f}. Focus can close this."
        )


# ===============================
# INSIGHTS
# ===============================

st.markdown("## 💡 Management Insights")


best = filtered.sort_values("Achievement %", ascending=False).head(3)
worst = filtered.sort_values("Achievement %").head(3)


c1, c2 = st.columns(2)


with c1:

    st.markdown("### 🌟 Top Performers")

    st.dataframe(
        best[["OUTLET", "Month", "Achievement %"]],
        use_container_width=True
    )


with c2:

    st.markdown("### ⚠️ Focus Areas")

    st.dataframe(
        worst[["OUTLET", "Month", "Achievement %"]],
        use_container_width=True
    )


# ===============================
# FOOTER
# ===============================

st.markdown("---")
st.markdown("📊 Prepared for Management Review")
