import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Outlet Performance Dashboard", layout="wide")
st.title("📈 Outlet Performance Dashboard")

# ==============================
# FILE PATH
# ==============================
FILE_PATH = "STREAMLIT_GP_REPORT.xlsx"  # <-- Replace with your file path

@st.cache_data
def load_data(path):
    return pd.read_excel(path, engine="openpyxl")

# ==============================
# LOAD DATA
# ==============================
try:
    df = load_data(FILE_PATH)
except FileNotFoundError:
    st.error(f"❌ File not found: {FILE_PATH}")
    st.stop()

# ==============================
# CLEAN COLUMNS
# ==============================
df.columns = df.columns.str.strip()
df["OUTLET"] = df["OUTLET"].astype(str).str.strip().str.upper()
df["CLASS"] = df["CLASS"].astype(str).str.strip()

# ==============================
# AREA CLASSIFICATION
# ==============================
labour_outlets = [
    "AZHAR AL MADINA HYPERMARKET",
    "AZHAR GENERAL TRADING",
    "BLUE PEARL SUPERMARKET",
    "FIDA AL MADINA HYPERMARKET",
    "HADEQAT AL MADINA HYPERMARKET LLC",
    "HILAL AL MADINA HYPERMARKET LLC",
    "SHAMS AL MADINA HYPERMARKET LLC"
]

df["AREA_TYPE"] = df["OUTLET"].apply(lambda x: "Labour" if x in labour_outlets else "Family")

# ==============================
# CATEGORY COLUMN MAPPING
# ==============================
categories = {
    "Department": {"sales": "DEPARTMENT Total Sales", "margin": "DEPARTMENT Margin (%)", "profit": "DEPARTMENT Total Profit"},
    "FMCG Food": {"sales": "FMCG FOOD Total Sales", "margin": "FMCG FOOD Margin (%)", "profit": "FMCG FOOD Total Profit"},
    "FMCG Non Food": {"sales": "FMCG NON FOOD Total Sales", "margin": "FMCG NON FOOD Margin (%)", "profit": "FMCG NON FOOD Total Profit"},
    "Fresh": {"sales": "FRESH Total Sales", "margin": "FRESH Margin (%)", "profit": "FRESH Total Profit"},
    "Mobile": {"sales": "MOBILE & ACCESSORIES Total Sales", "margin": "MOBILE & ACCESSORIES Margin (%)", "profit": "MOBILE & ACCESSORIES Total Profit"},
    "Services": {"sales": "SERVICES Total Sales", "margin": "SERVICES Margin (%)", "profit": "SERVICES Total Profit"}
}

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.header("📊 Dashboard Filters")
page = st.sidebar.selectbox("Select View", ["Outlet Wise", "Area Wise"])
selected_category = st.sidebar.multiselect("Select Categories", list(categories.keys()), default=list(categories.keys()))
area_filter = st.sidebar.multiselect("Select Area Type", df["AREA_TYPE"].unique(), default=df["AREA_TYPE"].unique())

# ==============================
# APPLY AREA FILTER
# ==============================
filtered_df = df[df["AREA_TYPE"].isin(area_filter)].copy()

# ==============================
# APPLY PAGE FILTER
# ==============================
if page == "Outlet Wise":
    outlet = st.sidebar.selectbox("Select Outlet", sorted(filtered_df["OUTLET"].unique()))
    filtered_df = filtered_df[filtered_df["OUTLET"] == outlet]
else:
    area = st.sidebar.selectbox("Select Area", sorted(filtered_df["AREA_TYPE"].unique()))
    filtered_df = filtered_df[filtered_df["AREA_TYPE"] == area]

# ==============================
# KPI CALCULATION
# ==============================
total_sales = 0
total_profit = 0
avg_margin = 0
count = 0

for cat in selected_category:
    if categories[cat]["sales"] in filtered_df.columns:
        total_sales += filtered_df[categories[cat]["sales"]].sum()
        total_profit += filtered_df[categories[cat]["profit"]].sum()
        avg_margin += filtered_df[categories[cat]["margin"]].mean()
        count += 1

avg_margin = avg_margin / count if count > 0 else 0

# ==============================
# KPI DISPLAY
# ==============================
k1, k2, k3 = st.columns(3)
k1.metric("💰 Total Sales", f"{total_sales:,.0f}")
k2.metric("📊 Total Profit", f"{total_profit:,.0f}")
k3.metric("📈 Avg Margin %", f"{avg_margin:.2f}%")
st.divider()

# ==============================
# CATEGORY WISE SUMMARY
# ==============================
category_data = []
for cat in selected_category:
    sales = filtered_df[categories[cat]["sales"]].sum()
    profit = filtered_df[categories[cat]["profit"]].sum()
    margin = filtered_df[categories[cat]["margin"]].mean()
    if sales > 0:
        category_data.append({"Category": cat, "Sales": sales, "Profit": profit, "Margin": margin})

cat_df = pd.DataFrame(category_data)

st.subheader("📌 Category Performance")
c1, c2 = st.columns(2)

if not cat_df.empty:
    fig1 = px.bar(cat_df, x="Category", y="Sales", title="Sales by Category")
    st.plotly_chart(fig1, use_container_width=True)
    fig2 = px.bar(cat_df, x="Category", y="Profit", title="Profit by Category")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("⚠️ No category data to display")

st.divider()

# ==============================
# CLASS WISE PERFORMANCE
# ==============================
st.subheader("🏷️ Class Performance")
class_data = []

for cls in filtered_df["CLASS"].unique():
    cls_df = filtered_df[filtered_df["CLASS"] == cls]
    sales = sum(cls_df[categories[cat]["sales"]].sum() for cat in selected_category if categories[cat]["sales"] in cls_df.columns)
    if sales > 0:
        class_data.append({"Class": cls, "Sales": sales})

class_df = pd.DataFrame(class_data)
if not class_df.empty:
    fig3 = px.bar(class_df, x="Class", y="Sales", title="Sales by Class (Zero Removed)")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("⚠️ No class data to display")

st.divider()

# ==============================
# AREA COMPARISON
# ==============================
st.subheader("📍 Labour vs Family Comparison")
area_summary = []

for area in df["AREA_TYPE"].unique():
    temp = df[df["AREA_TYPE"] == area]
    sales = sum(temp[categories[cat]["sales"]].sum() for cat in categories.keys() if categories[cat]["sales"] in temp.columns)
    profit = sum(temp[categories[cat]["profit"]].sum() for cat in categories.keys() if categories[cat]["profit"] in temp.columns)
    area_summary.append({"Area": area, "Sales": sales, "Profit": profit})

area_df = pd.DataFrame(area_summary)
c3, c4 = st.columns(2)
fig4 = px.bar(area_df, x="Area", y="Sales", title="Sales: Labour vs Family")
st.plotly_chart(fig4, use_container_width=True)
fig5 = px.bar(area_df, x="Area", y="Profit", title="Profit: Labour vs Family")
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ==============================
# DETAILED TABLE
# ==============================
st.subheader("📋 Detailed Data")
st.dataframe(filtered_df, use_container_width=True)

# ==============================
# FOOTER
# ==============================
st.caption("Developed for Outlet Performance Analysis | Salman Faris")
