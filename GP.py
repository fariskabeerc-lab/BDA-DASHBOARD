import streamlit as st
import pandas as pd
import plotly.express as px


# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Outlet Performance Dashboard", layout="wide")


# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    return pd.read_excel("STREAMLIT_GP_REPORT.Xlsx", engine="openpyxl")


df = load_data()


# ==============================
# CLEAN & RENAME COLUMNS
# ==============================

# Remove spaces from headers
df.columns = df.columns.str.strip()

# Rename Company Name → OUTLET
if "Company Name" in df.columns:
    df.rename(columns={"Company Name": "OUTLET"}, inplace=True)

# Rename Class → CLASS
if "Class" in df.columns:
    df.rename(columns={"Class": "CLASS"}, inplace=True)

# Safety check
required_cols = ["OUTLET", "CLASS"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"❌ Missing column: {col}")
        st.write("Available columns:", df.columns.tolist())
        st.stop()


# Clean outlet values
df["OUTLET"] = df["OUTLET"].astype(str).str.strip().str.upper()


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


df["AREA_TYPE"] = df["OUTLET"].apply(
    lambda x: "Labour" if x in labour_outlets else "Family"
)


# ==============================
# CATEGORY COLUMN MAPPING
# ==============================

categories = {

    "Department": {
        "sales": "DEPARTMENT Total Sales",
        "margin": "DEPARTMENT Margin (%)",
        "profit": "DEPARTMENT Total Profit"
    },

    "FMCG Food": {
        "sales": "FMCG FOOD Total Sales",
        "margin": "FMCG FOOD Margin (%)",
        "profit": "FMCG FOOD Total Profit"
    },

    "FMCG Non Food": {
        "sales": "FMCG NON FOOD Total Sales",
        "margin": "FMCG NON FOOD Margin (%)",
        "profit": "FMCG NON FOOD Total Profit"
    },

    "Fresh": {
        "sales": "FRESH Total Sales",
        "margin": "FRESH Margin (%)",
        "profit": "FRESH Total Profit"
    },

    "Mobile": {
        "sales": "MOBILE & ACCESSORIES Total Sales",
        "margin": "MOBILE & ACCESSORIES Margin (%)",
        "profit": "MOBILE & ACCESSORIES Total Profit"
    },

    "Services": {
        "sales": "SERVICES Total Sales",
        "margin": "SERVICES Margin (%)",
        "profit": "SERVICES Total Profit"
    }
}


# ==============================
# SIDEBAR FILTERS
# ==============================

st.sidebar.header("📊 Dashboard Filters")

page = st.sidebar.selectbox(
    "Select View",
    ["Outlet Wise", "Area Wise"]
)


selected_category = st.sidebar.multiselect(
    "Select Categories",
    list(categories.keys()),
    default=list(categories.keys())
)


area_filter = st.sidebar.multiselect(
    "Select Area Type",
    df["AREA_TYPE"].unique(),
    default=df["AREA_TYPE"].unique()
)


# ==============================
# APPLY FILTERS
# ==============================

filtered_df = df[df["AREA_TYPE"].isin(area_filter)].copy()


if page == "Outlet Wise":

    outlet = st.sidebar.selectbox(
        "Select Outlet",
        sorted(filtered_df["OUTLET"].unique())
    )

    filtered_df = filtered_df[filtered_df["OUTLET"] == outlet]

else:

    area = st.sidebar.selectbox(
        "Select Area",
        sorted(filtered_df["AREA_TYPE"].unique())
    )

    filtered_df = filtered_df[filtered_df["AREA_TYPE"] == area]


# ==============================
# KPI CALCULATION
# ==============================

total_sales = 0
total_profit = 0
avg_margin = 0
count = 0


for cat in selected_category:

    total_sales += filtered_df[categories[cat]["sales"]].sum()
    total_profit += filtered_df[categories[cat]["profit"]].sum()

    avg_margin += filtered_df[categories[cat]["margin"]].mean()
    count += 1


if count > 0:
    avg_margin = avg_margin / count


# ==============================
# PAGE TITLE
# ==============================

st.title("📈 Outlet Performance Dashboard")


# ==============================
# KPI DISPLAY
# ==============================

k1, k2, k3 = st.columns(3)

k1.metric("💰 Total Sales", f"{total_sales:,.0f}")
k2.metric("📊 Total Profit", f"{total_profit:,.0f}")
k3.metric("📈 Avg Margin %", f"{avg_margin:.2f}%")


st.divider()


# ==============================
# CATEGORY SUMMARY
# ==============================

category_data = []


for cat in selected_category:

    sales = filtered_df[categories[cat]["sales"]].sum()
    profit = filtered_df[categories[cat]["profit"]].sum()
    margin = filtered_df[categories[cat]["margin"]].mean()


    if sales > 0:

        category_data.append({
            "Category": cat,
            "Sales": sales,
            "Profit": profit,
            "Margin": margin
        })


cat_df = pd.DataFrame(category_data)


# ==============================
# CATEGORY GRAPHS
# ==============================

st.subheader("📌 Category Performance")

c1, c2 = st.columns(2)


with c1:

    fig1 = px.bar(
        cat_df,
        x="Category",
        y="Sales",
        title="Sales by Category"
    )

    st.plotly_chart(fig1, use_container_width=True)


with c2:

    fig2 = px.bar(
        cat_df,
        x="Category",
        y="Profit",
        title="Profit by Category"
    )

    st.plotly_chart(fig2, use_container_width=True)


st.divider()


# ==============================
# CLASS PERFORMANCE
# ==============================

st.subheader("🏷️ Class Performance")


class_data = []


for cls in filtered_df["CLASS"].unique():

    cls_df = filtered_df[filtered_df["CLASS"] == cls]

    sales = 0


    for cat in selected_category:
        sales += cls_df[categories[cat]["sales"]].sum()


    if sales > 0:

        class_data.append({
            "Class": cls,
            "Sales": sales
        })


class_df = pd.DataFrame(class_data)


fig3 = px.bar(
    class_df,
    x="Class",
    y="Sales",
    title="Sales by Class (Zero Removed)"
)

st.plotly_chart(fig3, use_container_width=True)


st.divider()


# ==============================
# LABOUR vs FAMILY
# ==============================

st.subheader("📍 Labour vs Family Comparison")


area_summary = []


for area in df["AREA_TYPE"].unique():

    temp = df[df["AREA_TYPE"] == area]

    sales = 0
    profit = 0


    for cat in categories.keys():

        sales += temp[categories[cat]["sales"]].sum()
        profit += temp[categories[cat]["profit"]].sum()


    area_summary.append({
        "Area": area,
        "Sales": sales,
        "Profit": profit
    })


area_df = pd.DataFrame(area_summary)


c3, c4 = st.columns(2)


with c3:

    fig4 = px.bar(
        area_df,
        x="Area",
        y="Sales",
        title="Sales: Labour vs Family"
    )

    st.plotly_chart(fig4, use_container_width=True)


with c4:

    fig5 = px.bar(
        area_df,
        x="Area",
        y="Profit",
        title="Profit: Labour vs Family"
    )

    st.plotly_chart(fig5, use_container_width=True)


st.divider()


# ==============================
# TABLE
# ==============================

st.subheader("📋 Detailed Data")

st.dataframe(filtered_df, use_container_width=True)


# ==============================
# FOOTER
# ==============================

st.caption("Developed for Outlet Performance Analysis | Salman Faris")
