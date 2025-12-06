import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------------
# BASIC PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Business Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Sample - Superstore.csv", encoding="latin1")
    # standardise column names for easier handling
    df.columns = [c.strip() for c in df.columns]

    # make sure order date is datetime
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
        df["Year-Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# keep original for reference
base_df = df.copy()

# ------------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------------
st.sidebar.title("Filters")

# Date range filter
if "Order Date" in df.columns:
    min_date = df["Order Date"].min()
    max_date = df["Order Date"].max()
    date_range = st.sidebar.date_input(
        "Order date range",
        [min_date, max_date]
    )
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df["Order Date"] >= pd.to_datetime(start_date)) &
                (df["Order Date"] <= pd.to_datetime(end_date))]

# Region filter
if "Region" in df.columns:
    regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
    sel_region = st.sidebar.multiselect("Region", regions, default=["All"])
    if "All" not in sel_region:
        df = df[df["Region"].isin(sel_region)]

# Category filter
if "Category" in df.columns:
    cats = ["All"] + sorted(df["Category"].dropna().unique().tolist())
    sel_cat = st.sidebar.multiselect("Category", cats, default=["All"])
    if "All" not in sel_cat:
        df = df[df["Category"].isin(sel_cat)]

# Segment filter (optional)
if "Segment" in df.columns:
    segs = ["All"] + sorted(df["Segment"].dropna().unique().tolist())
    sel_seg = st.sidebar.multiselect("Segment", segs, default=["All"])
    if "All" not in sel_seg:
        df = df[df["Segment"].isin(sel_seg)]

st.sidebar.markdown("---")
st.sidebar.write(f"Rows after filters: **{len(df):,}**")

# ------------------------------------------------------------------
# HEADER
# ------------------------------------------------------------------
st.title("Business Analytics Dashboard")
st.caption("Sample - Superstore data visualization using Streamlit + Plotly")

# ------------------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------------------
sales_col = "Sales"
profit_col = "Profit"

total_sales = df[sales_col].sum() if sales_col in df.columns else 0
total_profit = df[profit_col].sum() if profit_col in df.columns else 0
orders = df["Order ID"].nunique() if "Order ID" in df.columns else len(df)

profit_pct = (total_profit / total_sales * 100) if total_sales != 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales", f"${total_sales:,.2f}")
kpi2.metric("Total Profit", f"${total_profit:,.2f}")
kpi3.metric("Profit %", f"{profit_pct:,.2f}%")
kpi4.metric("Unique Orders", f"{orders:,}")

# ------------------------------------------------------------------
# DATA PREVIEW + DOWNLOAD
# ------------------------------------------------------------------
st.subheader("Data preview")
st.dataframe(df.head(20), use_container_width=True)

st.download_button(
    label="Download filtered data as CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_superstore.csv",
    mime="text/csv"
)

st.markdown("---")

# ------------------------------------------------------------------
# ROW 1: TIME SERIES
# ------------------------------------------------------------------
if "Year-Month" in df.columns and sales_col in df.columns:
    ts = (
        df.groupby("Year-Month")[sales_col]
        .sum()
        .reset_index()
        .sort_values("Year-Month")
    )
    fig_ts = px.line(
        ts,
        x="Year-Month",
        y=sales_col,
        title="Monthly Sales Trend",
        markers=True
    )
    fig_ts.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_ts, use_container_width=True)

# ------------------------------------------------------------------
# ROW 2: CATEGORY & SUB-CATEGORY
# ------------------------------------------------------------------
row2_col1, row2_col2 = st.columns(2)

if "Category" in df.columns and sales_col in df.columns:
    cat_sales = (
        df.groupby("Category")[sales_col]
        .sum()
        .reset_index()
        .sort_values("Sales", ascending=False)
    )
    fig_cat = px.bar(
        cat_sales,
        x="Category",
        y="Sales",
        title="Sales by Category",
        text_auto=".2s"
    )
    row2_col1.plotly_chart(fig_cat, use_container_width=True)

if "Sub-Category" in df.columns and profit_col in df.columns:
    sub_profit = (
        df.groupby("Sub-Category")[profit_col]
        .sum()
        .reset_index()
        .sort_values("Profit", ascending=False)
        .head(15)
    )
    fig_sub = px.bar(
        sub_profit,
        x="Sub-Category",
        y="Profit",
        title="Top 15 Sub-Categories by Profit"
    )
    fig_sub.update_layout(xaxis_tickangle=-45)
    row2_col2.plotly_chart(fig_sub, use_container_width=True)

# ------------------------------------------------------------------
# ROW 3: REGION & PROFIT vs SALES
# ------------------------------------------------------------------
row3_col1, row3_col2 = st.columns(2)

if "Region" in df.columns and sales_col in df.columns:
    reg_sales = (
        df.groupby("Region")[sales_col]
        .sum()
        .reset_index()
        .sort_values("Sales", ascending=False)
    )
    fig_reg = px.bar(
        reg_sales,
        x="Region",
        y="Sales",
        title="Sales by Region",
        text_auto=".2s"
    )
    row3_col1.plotly_chart(fig_reg, use_container_width=True)

if sales_col in df.columns and profit_col in df.columns:
    fig_scatter = px.scatter(
        df,
        x=sales_col,
        y=profit_col,
        color="Category" if "Category" in df.columns else None,
        hover_data=["Customer Name", "Region"] if "Customer Name" in df.columns else None,
        title="Profit vs Sales (by Category)",
        trendline="ols"
    )
    row3_col2.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------------
# TOP CUSTOMERS
# ------------------------------------------------------------------
if "Customer Name" in df.columns and sales_col in df.columns:
    st.subheader("Top 10 Customers by Sales")
    top_cust = (
        df.groupby("Customer Name")[sales_col]
        .sum()
        .reset_index()
        .sort_values("Sales", ascending=False)
        .head(10)
    )
    st.dataframe(top_cust, use_container_width=True)

