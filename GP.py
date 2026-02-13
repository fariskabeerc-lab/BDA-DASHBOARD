import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Supplier Rebate Dashboard",
    layout="wide"
)

# ==============================
# HIDE STREAMLIT UI
# ==============================
st.markdown("""
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==============================
# FILE PATH (CHANGE THIS)
# ==============================
FILE_PATH = r"BDA STREAMLIT.xlsx"


# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    df = pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()
    return df


df = load_data()


# ==============================
# CALCULATIONS
# ==============================

def calculate_rebate(row, purchase):

    rebate = 0

    slabs = [
        ("SLAB A", "SLAB A ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB B", "SLAB B ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB C", "SLAB C ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB D", "SLAB D ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB E", "SLAB E ACHIEVE PAYABLE AMOUNT%"),
    ]

    for slab, pct in slabs:

        if row[slab] > 0 and purchase >= row[slab]:
            rebate = purchase * (row[pct] / 100)

    return rebate


# ==============================
# SIDEBAR
# ==============================

st.sidebar.header("🔍 Filter")

supplier_list = ["All"] + sorted(df["supplier"].unique().tolist())

selected_supplier = st.sidebar.selectbox(
    "Select Supplier",
    supplier_list
)


# ==============================
# FILTER DATA
# ==============================

if selected_supplier == "All":
    data = df.copy()
else:
    data = df[df["supplier"] == selected_supplier]


# ==============================
# OVERALL INSIGHTS
# ==============================

total_target = data["BASE TARGET"].sum()
total_2025 = data["2025 TOTEL PURCHASE"].sum()
total_2026 = data["2026 TOTEL PURCHASE"].sum()

total_gap = total_target - total_2026


# Calculate total rebate
total_rebate = 0

for i, row in data.iterrows():
    total_rebate += calculate_rebate(row, row["2026 TOTEL PURCHASE"])


# ==============================
# HEADER
# ==============================

st.title("📊 Supplier Progressive Rebate Dashboard")
st.markdown("---")


# ==============================
# KPI CARDS
# ==============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("🎯 Total Target", f"{total_target:,.0f}")
col2.metric("🛒 2026 Purchase", f"{total_2026:,.0f}")
col3.metric("📈 Gap to Target", f"{total_gap:,.0f}")
col4.metric("💰 Est. Rebate", f"{total_rebate:,.0f}")


st.markdown("---")


# ==============================
# SUPPLIER DETAILS
# ==============================

if selected_supplier != "All":

    row = data.iloc[0]

    st.subheader(f"📌 Supplier: {selected_supplier}")

    col1, col2, col3 = st.columns(3)

    col1.metric("2025 Purchase", f"{row['2025 TOTEL PURCHASE']:,.0f}")
    col2.metric("2026 Purchase", f"{row['2026 TOTEL PURCHASE']:,.0f}")
    col3.metric("Base Target", f"{row['BASE TARGET']:,.0f}")


    gap = row["BASE TARGET"] - row["2026 TOTEL PURCHASE"]

    st.info(f"📉 Remaining to reach Base Target: {gap:,.0f}")


# ==============================
# SLAB ANALYSIS
# ==============================

st.subheader("🏆 Slab Progress")

slab_data = []

for i, row in data.iterrows():

    purchase = row["2026 TOTEL PURCHASE"]

    slabs = [
        ("SLAB A", "SLAB A ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB B", "SLAB B ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB C", "SLAB C ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB D", "SLAB D ACHIEVE PAYABLE AMOUNT%"),
        ("SLAB E", "SLAB E ACHIEVE PAYABLE AMOUNT%"),
    ]

    for slab, pct in slabs:

        if row[slab] > 0:

            required = row[slab]
            remaining = max(0, required - purchase)

            status = "Achieved" if purchase >= required else "Pending"

            rebate_value = 0

            if purchase >= required:
                rebate_value = purchase * (row[pct] / 100)

            slab_data.append({
                "Supplier": row["supplier"],
                "Slab": slab,
                "Target": required,
                "Current Purchase": purchase,
                "Remaining": remaining,
                "Rebate %": row[pct],
                "Rebate Value": rebate_value,
                "Status": status
            })


slab_df = pd.DataFrame(slab_data)


# ==============================
# TABLE
# ==============================

st.dataframe(
    slab_df,
    use_container_width=True,
    height=400
)


# ==============================
# SLAB BAR CHART (REMAINING)
# ==============================

st.subheader("📊 Remaining Purchase to Achieve Slabs")

pending = slab_df[slab_df["Status"] == "Pending"]

if not pending.empty:

    fig, ax = plt.subplots()

    ax.bar(
        pending["Slab"] + " (" + pending["Supplier"] + ")",
        pending["Remaining"]
    )

    ax.set_xlabel("Slabs")
    ax.set_ylabel("Remaining Purchase")
    ax.set_title("Remaining to Achieve Slabs")

    plt.xticks(rotation=45)

    st.pyplot(fig)

else:
    st.success("✅ All slabs achieved!")


# ==============================
# PURCHASE DISTRIBUTION PIE
# ==============================

st.subheader("🥧 Purchase Distribution (2026)")

purchase_data = data.groupby("supplier")["2026 TOTEL PURCHASE"].sum()

fig2, ax2 = plt.subplots()

ax2.pie(
    purchase_data,
    labels=purchase_data.index,
    autopct='%1.1f%%',
    startangle=90
)

ax2.axis("equal")

st.pyplot(fig2)


# ==============================
# YEAR COMPARISON
# ==============================

st.subheader("📈 2025 vs 2026 Comparison")

compare_df = data.groupby("supplier").agg({
    "2025 TOTEL PURCHASE": "sum",
    "2026 TOTEL PURCHASE": "sum"
})

fig3, ax3 = plt.subplots()

compare_df.plot(kind="bar", ax=ax3)

ax3.set_ylabel("Purchase Value")
ax3.set_title("2025 vs 2026 Purchase")

plt.xticks(rotation=45)

st.pyplot(fig3)


# ==============================
# FINAL INSIGHTS
# ==============================

st.markdown("---")
st.subheader("📌 Key Insights")

achieved = slab_df[slab_df["Status"] == "Achieved"].shape[0]
pending_count = slab_df[slab_df["Status"] == "Pending"].shape[0]

st.write(f"✅ Achieved Slabs: {achieved}")
st.write(f"⏳ Pending Slabs: {pending_count}")
st.write(f"💰 Total Expected Rebate: {total_rebate:,.0f}")
st.write(f"📦 Total Purchase Needed to Reach Targets: {max(0, total_gap):,.0f}")


st.success("Dashboard Loaded Successfully ✅")
