
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page configuration
st.set_page_config(
    page_title="AI Inventory Forecasting",
    page_icon="📦",
    layout="wide"
)

# Dashboard title
st.title("📦 AI-Based Inventory and Demand Forecasting")
st.write("Smart inventory planning and demand analysis for supply chains.")

# Load CSV files
@st.cache_data
def load_data():
    statistics = pd.read_csv("outputs/product_statistics.csv")
    forecasts = pd.read_csv("outputs/forecast_results.csv")
    models = pd.read_csv("outputs/model_comparison.csv")
    return statistics, forecasts, models

try:
    statistics, forecasts, models = load_data()

    # Standardize column names
    statistics.columns = statistics.columns.str.lower().str.strip()
    forecasts.columns = forecasts.columns.str.lower().str.strip()
    models.columns = models.columns.str.lower().str.strip()

    # Sidebar
    st.sidebar.header("Dashboard Controls")

    products = sorted(forecasts["item"].unique())
    selected_product = st.sidebar.selectbox(
        "Select Product",
        products
    )

    # Filter selected product
    product_forecast = forecasts[
        forecasts["item"] == selected_product
    ]

    product_stats = statistics[
        statistics["item"] == selected_product
    ]

    # Main metrics
    st.subheader("Project Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Products", len(products))

    with col2:
        st.metric("Forecast Records", len(forecasts))

    with col3:
        if "mae" in models.columns:
            st.metric(
                "Best Model MAE",
                round(models["mae"].min(), 2)
            )
        else:
            st.metric("Forecast Models", len(models))

    st.divider()

    # Product statistics
    st.subheader("Product Demand Statistics")

    if not product_stats.empty:
        st.dataframe(product_stats, use_container_width=True)

        stat_cols = ["mean", "min", "max"]
        available = [
            col for col in stat_cols
            if col in product_stats.columns
        ]

        if available:
            chart_data = product_stats.melt(
                id_vars=["item"],
                value_vars=available,
                var_name="Statistic",
                value_name="Sales"
            )

            fig = px.bar(
                chart_data,
                x="Statistic",
                y="Sales",
                color="Statistic",
                title=f"Demand Statistics - Product {selected_product}"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Actual vs Predicted Sales
    st.subheader("Actual vs Predicted Sales")

    fig = px.line(
        product_forecast,
        y=["actual_sales", "predicted_sales"],
        title=f"Actual and Predicted Sales - Product {selected_product}",
        labels={
            "value": "Sales",
            "index": "Test Record",
            "variable": "Sales Type"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    # Forecast comparison
    st.divider()
    st.subheader("Forecast Model Comparison")

    st.dataframe(models, use_container_width=True)

    # Detect model and MAE columns
    mae_col = next(
        (c for c in models.columns if "mae" in c),
        None
    )

    model_col = next(
        (c for c in models.columns
         if "model" in c or "algorithm" in c),
        None
    )

    if mae_col and model_col:
        fig = px.bar(
            models,
            x=model_col,
            y=mae_col,
            color=model_col,
            title="Model Comparison using MAE"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Inventory planning section
    st.subheader("Inventory Planning")

    st.info(
        "Inventory optimization results will be displayed here "
        "after integrating the inventory calculations from the team."
    )

    st.success("Dashboard data loaded successfully!")

except Exception as e:
    st.error("Unable to load the dashboard data.")
    st.write("Please check the CSV filenames and column names.")
    st.write("Error:", e)
