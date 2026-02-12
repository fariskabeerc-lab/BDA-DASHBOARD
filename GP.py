import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
FILE_PATH = "your_file_path_here.xlsx"  # Update this to your actual file path
st.set_page_config(page_title="Retail Area & Outlet Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel(FILE_PATH)
    
    # Define Labour Area Outlets
    labour_outlets = [
        "AZHAR AL MADINA HYPERMARKET", "AZHAR GENERAL TRADING", 
        "BLUE PEARL SUPERMARKET", "FIDA AL MADINA HYPERMARKET", 
        "HADEQAT AL MADINA HYPERMARKET LLC", "HILAL AL MADINA HYPERMARKET LLC", 
        "SHAMS AL MADINA HYPERMARKET LLC"
    ]
    
    # Logic to create the AREA column dynamically
    df['AREA'] = df['OUTLET'].apply(lambda x: 'Labour' if str(x).strip() in labour_outlets else 'Family')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Dashboard Navigation")
page = st.sidebar.radio("Go to:", ["Outlet Analysis", "Area-Wise Performance"])

categories = ["DEPARTMENT", "FMCG FOOD", "FMCG NON FOOD", "FRESH", "MOBILE & ACCESSORIES", "SERVICES"]
selected_cat = st.sidebar.selectbox("Filter by Category", categories)

# --- PAGE 1: OUTLET ANALYSIS ---
if page == "Outlet Analysis":
    st.title("📊 Individual Outlet Insights")
    
    selected_outlet = st.selectbox("Select Outlet Name", df['OUTLET'].unique())
    row = df[df['OUTLET'] == selected_outlet].iloc[0]
    
    # KPIs for the selected Outlet
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric(f"{selected_cat} Sales", f"{row[selected_cat + ' Total Sales']:,.0f}")
    with kpi2:
        # Highlighting the GP (Total Profit)
        st.metric(f"{selected_cat} GP (Profit)", f"{row[selected_cat + ' Total Profit']:,.0f}", delta_color="normal")
    with kpi3:
        st.metric(f"{selected_cat} Margin", f"{row[selected_cat + ' Margin (%)']}%")

    st.divider()
    
    # Class Performance Chart
    st.subheader(f"Performance Breakdown: {selected_outlet}")
    # Compare Sales vs Profit for all major categories to see where the GP is highest
    comparison_data = []
    for cat in categories:
        comparison_data.append({
            "Category": cat,
            "Sales": row[f"{cat} Total Sales"],
            "GP": row[f"{cat} Total Profit"]
        })
    comp_df = pd.DataFrame(comparison_data)
    
    fig = px.bar(comp_df, x="Category", y=["Sales", "GP"], barmode="group",
                 title="Sales vs Gross Profit across all Classes",
                 color_discrete_map={"Sales": "#636EFA", "GP": "#00CC96"})
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: AREA-WISE PERFORMANCE ---
else:
    st.title("📍 Area Comparison: Labour vs. Family")
    
    # Aggregating data by Area
    area_summary = df.groupby('AREA')[[f"{selected_cat} Total Sales", f"{selected_cat} Total Profit"]].sum().reset_index()
    
    # Area KPIs
    col_labour, col_family = st.columns(2)
    
    with col_labour:
        labour_val = area_summary[area_summary['AREA'] == 'Labour'][f"{selected_cat} Total Profit"].values[0]
        st.subheader("🛠️ Labour Area")
        st.metric(f"Total {selected_cat} GP", f"{labour_val:,.0f}")
        
    with col_family:
        family_val = area_summary[area_summary['AREA'] == 'Family'][f"{selected_cat} Total Profit"].values[0]
        st.subheader("👨‍👩‍👧‍👦 Family Area")
        st.metric(f"Total {selected_cat} GP", f"{family_val:,.0f}")

    st.divider()

    # Visualizing Performance by Area
    st.subheader(f"Class Performance by Area ({selected_cat})")
    
    # Melt data for better plotting
    melted_area = df.groupby('AREA')[[f"{cat} Total Profit" for cat in categories]].sum().reset_index()
    melted_area = melted_area.melt(id_vars='AREA', var_name='Category', value_name='GP')
    melted_area['Category'] = melted_area['Category'].str.replace(' Total Profit', '')

    fig_area = px.bar(melted_area, x="Category", y="GP", color="AREA", barmode="group",
                      title="GP Comparison: Labour vs Family per Class")
    st.plotly_chart(fig_area, use_container_width=True)
    
    st.write("### Data Breakdown by Outlet in this Area")
    st.dataframe(df[df['AREA'] == st.radio("Show Outlets for:", ["Labour", "Family"])][['OUTLET', f"{selected_cat} Total Sales", f"{selected_cat} Total Profit", f"{selected_cat} Margin (%)"]])
