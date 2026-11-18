import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Inventory Forecasting",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Main title */
    .main-title {
        background: linear-gradient(90deg, #1f3553, #294d75);
        padding: 25px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }

    .main-title h1 {
        color: white;
        margin: 0;
        font-size: 38px;
    }

    .main-title p {
        color: #d9e8f5;
        margin-top: 8px;
        font-size: 16px;
    }

    /* Section headings */
    .section-title {
        background-color: #203752;
        color: white;
        padding: 12px 18px;
        border-radius: 8px;
        margin-top: 20px;
        margin-bottom: 15px;
        font-size: 22px;
        font-weight: 700;
    }

    /* Requirement cards */
    .requirement-card {
        background-color: #e7f1f7;
        border-radius: 12px;
        padding: 18px;
        min-height: 135px;
        border-left: 5px solid #20a7aa;
    }

    .requirement-number {
        background-color: #20a7aa;
        color: white;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 8px;
    }

    .requirement-title {
        font-weight: bold;
        color: #203752;
        font-size: 17px;
    }

    .requirement-text {
        color: #38526d;
        font-size: 14px;
        margin-top: 10px;
    }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #203752, #2c537c);
        color: white;
        padding: 20px;
        border-radius: 12px;
        min-height: 120px;
    }

    .kpi-label {
        color: #a9dce0;
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        color: white;
        font-size: 28px;
        font-weight: bold;
        margin-top: 8px;
    }

    .kpi-description {
        color: #d7e4ef;
        font-size: 12px;
        margin-top: 5px;
    }

    /* Status boxes */
    .status-good {
        background-color: #dff5e7;
        color: #176b36;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: bold;
    }

    .status-warning {
        background-color: #fff2cc;
        color: #8a6100;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: bold;
    }

    .status-danger {
        background-color: #fde2e2;
        color: #a32626;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: bold;
    }

    /* Small explanatory text */
    .info-text {
        color: #536b82;
        font-size: 14px;
    }

</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================

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

    # ========================================================
    # CHECK REQUIRED COLUMNS
    # ========================================================

    required_forecast_columns = [
        "item",
        "actual_sales",
        "predicted_sales"
    ]

    missing_columns = [
        col for col in required_forecast_columns
        if col not in forecasts.columns
    ]

    if missing_columns:
        st.error(
            f"Missing columns in forecast_results.csv: {missing_columns}"
        )
        st.stop()

    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.markdown("## 📦 Dashboard Controls")

    products = sorted(forecasts["item"].unique())

    selected_product = st.sidebar.selectbox(
        "Select Product",
        products
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown("### ⚙️ Inventory Parameters")

    current_stock = st.sidebar.number_input(
        "Current Stock (units)",
        min_value=0,
        value=100,
        step=10
    )

    lead_time = st.sidebar.number_input(
        "Lead Time (days)",
        min_value=1,
        value=7,
        step=1
    )

    safety_stock_days = st.sidebar.number_input(
        "Safety Stock (days)",
        min_value=0,
        value=3,
        step=1
    )

    ordering_cost = st.sidebar.number_input(
        "Ordering Cost / Order",
        min_value=0.0,
        value=50.0,
        step=10.0
    )

    holding_cost = st.sidebar.number_input(
        "Holding Cost / Unit",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

    stockout_cost = st.sidebar.number_input(
        "Stockout Cost / Unit",
        min_value=0.0,
        value=10.0,
        step=1.0
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 📈 Demand Surge Simulation")

    demand_surge = st.sidebar.slider(
        "Expected Demand Increase",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )

    # ========================================================
    # FILTER PRODUCT
    # ========================================================

    product_forecast = forecasts[
        forecasts["item"] == selected_product
    ].copy()

    product_stats = statistics[
        statistics["item"] == selected_product
    ].copy()

    # ========================================================
    # CALCULATE FORECAST VALUES
    # ========================================================

    actual_mean = product_forecast["actual_sales"].mean()

    predicted_mean = product_forecast["predicted_sales"].mean()

    predicted_mean_surge = (
        predicted_mean * (1 + demand_surge / 100)
    )

    # Assume sales values represent daily demand
    daily_demand = predicted_mean_surge

    weekly_demand = daily_demand * 7

    five_week_demand = weekly_demand * 5

    # Safety stock
    safety_stock = daily_demand * safety_stock_days

    # Reorder point
    reorder_point = (
        daily_demand * lead_time
        + safety_stock
    )

    # Recommended reorder quantity
    recommended_order = max(
        0,
        round(
            weekly_demand + safety_stock - current_stock
        )
    )

    # Stockout probability approximation
    if current_stock <= 0:
        stockout_probability = 100
    elif current_stock < reorder_point:
        stockout_probability = min(
            95,
            round(
                ((reorder_point - current_stock)
                 / reorder_point) * 100
            )
        )
    else:
        stockout_probability = max(
            0,
            round(
                ((reorder_point - current_stock)
                 / reorder_point) * 20
            )
        )

    # Forecast accuracy
    mae = np.mean(
        np.abs(
            product_forecast["actual_sales"]
            - product_forecast["predicted_sales"]
        )
    )

    actual_avg = max(abs(actual_mean), 1)

    forecast_accuracy = max(
        0,
        min(
            100,
            100 - ((mae / actual_avg) * 100)
        )
    )

    # Estimated inventory cost
    estimated_holding = (
        current_stock * holding_cost
    )

    estimated_stockout = (
        stockout_probability / 100
        * max(daily_demand, 1)
        * stockout_cost
    )

    estimated_total_cost = (
        ordering_cost
        + estimated_holding
        + estimated_stockout
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown("""
    <div class="main-title">
        <h1>📦 AI-Based Inventory and Demand Forecasting</h1>
        <p>
        AI-powered demand prediction, reorder alerts,
        stockout analysis and inventory planning
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # PROJECT REQUIREMENTS
    # ========================================================

    st.markdown(
        '<div class="section-title">🎯 What Does Our System Deliver?</div>',
        unsafe_allow_html=True
    )

    req1, req2, req3 = st.columns(3)

    with req1:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">1</span>
            <span class="requirement-title">Demand Prediction</span>
            <div class="requirement-text">
                Forecast future demand for the selected product
                using the project's forecasting models.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with req2:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">2</span>
            <span class="requirement-title">Reorder Alerts</span>
            <div class="requirement-text">
                Identify products that are at or near
                their reorder point.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with req3:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">3</span>
            <span class="requirement-title">Stockout Probability</span>
            <div class="requirement-text">
                Estimate the risk of running out of inventory
                before replenishment.
            </div>
        </div>
        """, unsafe_allow_html=True)

    req4, req5, req6 = st.columns(3)

    with req4:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">4</span>
            <span class="requirement-title">Order Recommendations</span>
            <div class="requirement-text">
                Recommend suitable replenishment quantities
                based on forecast demand.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with req5:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">5</span>
            <span class="requirement-title">Cost Estimation</span>
            <div class="requirement-text">
                Estimate ordering, holding and potential
                stockout costs.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with req6:
        st.markdown("""
        <div class="requirement-card">
            <span class="requirement-number">6</span>
            <span class="requirement-title">Interactive Dashboard</span>
            <div class="requirement-text">
                Display important inventory and forecasting
                information in one place.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # KPI DASHBOARD
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Proposed Dashboard</div>',
        unsafe_allow_html=True
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">TOTAL PRODUCTS</div>
            <div class="kpi-value">{len(products)}</div>
            <div class="kpi-description">Products monitored</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">PREDICTED DAILY DEMAND</div>
            <div class="kpi-value">{daily_demand:.1f}</div>
            <div class="kpi-description">Units / day</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">REORDER POINT</div>
            <div class="kpi-value">{reorder_point:.0f}</div>
            <div class="kpi-description">Units</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">RECOMMENDED ORDER</div>
            <div class="kpi-value">{recommended_order}</div>
            <div class="kpi-description">Units to replenish</div>
        </div>
        """, unsafe_allow_html=True)

    # Second KPI row
    k5, k6, k7, k8 = st.columns(4)

    with k5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">FORECAST ACCURACY</div>
            <div class="kpi-value">{forecast_accuracy:.1f}%</div>
            <div class="kpi-description">Based on MAE</div>
        </div>
        """, unsafe_allow_html=True)

    with k6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">STOCKOUT PROBABILITY</div>
            <div class="kpi-value">{stockout_probability}%</div>
            <div class="kpi-description">Estimated risk</div>
        </div>
        """, unsafe_allow_html=True)

    with k7:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">SAFETY STOCK</div>
            <div class="kpi-value">{safety_stock:.0f}</div>
            <div class="kpi-description">Units</div>
        </div>
        """, unsafe_allow_html=True)

    with k8:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">EST. INVENTORY COST</div>
            <div class="kpi-value">₹{estimated_total_cost:,.0f}</div>
            <div class="kpi-description">Estimated cycle cost</div>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # INVENTORY STATUS
    # ========================================================

    st.markdown(
        '<div class="section-title">🚦 Inventory Status</div>',
        unsafe_allow_html=True
    )

    if current_stock <= 0:
        status = "🔴 OUT OF STOCK"
        status_class = "status-danger"
        status_text = "Immediate replenishment required."

    elif current_stock < reorder_point:
        status = "🟡 REORDER REQUIRED"
        status_class = "status-warning"
        status_text = "Current stock is below the calculated reorder point."

    else:
        status = "🟢 STOCK LEVEL HEALTHY"
        status_class = "status-good"
        status_text = "Current stock is above the calculated reorder point."

    st.markdown(
        f"""
        <div class="{status_class}">
            {status}<br>
            <span style="font-weight:normal">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # DEMAND FORECAST
    # ========================================================

    st.markdown(
        '<div class="section-title">📈 Demand Prediction</div>',
        unsafe_allow_html=True
    )

    col_chart, col_info = st.columns([2, 1])

    with col_chart:

        forecast_chart = product_forecast.copy()

        forecast_chart["Record"] = range(
            1,
            len(forecast_chart) + 1
        )

        fig = px.line(
            forecast_chart,
            x="Record",
            y=["actual_sales", "predicted_sales"],
            markers=True,
            title=f"Actual vs Predicted Sales — Product {selected_product}",
            labels={
                "value": "Sales / Demand",
                "variable": "Sales Type"
            }
        )

        fig.update_layout(
            height=400,
            legend_title="",
            plot_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col_info:

        st.markdown("### 📌 Forecast Summary")

        st.metric(
            "Average Actual Demand",
            f"{actual_mean:.1f} units"
        )

        st.metric(
            "Average Predicted Demand",
            f"{predicted_mean:.1f} units"
        )

        st.metric(
            "Forecast MAE",
            f"{mae:.2f}"
        )

        st.metric(
            "Forecast Accuracy",
            f"{forecast_accuracy:.1f}%"
        )

    # ========================================================
    # 5 WEEK PROJECTED DEMAND
    # ========================================================

    st.markdown(
        '<div class="section-title">📅 5-Week Projected Demand</div>',
        unsafe_allow_html=True
    )

    weeks = ["W1", "W2", "W3", "W4", "W5"]

    # Create slightly varying projections based on recent forecast trend
    recent_predictions = product_forecast[
        "predicted_sales"
    ].tail(5).tolist()

    if len(recent_predictions) < 5:
        recent_predictions = [
            predicted_mean
        ] * 5

    projected_values = [
        value * (1 + demand_surge / 100)
        for value in recent_predictions
    ]

    weekly_df = pd.DataFrame({
        "Week": weeks,
        "Projected Demand": projected_values
    })

    fig = px.bar(
        weekly_df,
        x="Week",
        y="Projected Demand",
        text_auto=".1f",
        title="Projected Demand for Next 5 Weeks"
    )

    fig.update_layout(
        height=350,
        plot_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # DEMAND SURGE
    # ========================================================

    st.markdown(
        f"""
        <div class="info-text">
        📈 Demand Surge Simulation: <b>+{demand_surge}%</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # REORDER ALERTS
    # ========================================================

    st.markdown(
        '<div class="section-title">🚨 Reorder Alerts</div>',
        unsafe_allow_html=True
    )

    # Create inventory overview for all products
    inventory_rows = []

    for product in products:

        p_data = forecasts[
            forecasts["item"] == product
        ]

        p_daily_demand = p_data[
            "predicted_sales"
        ].mean()

        p_daily_demand *= (
            1 + demand_surge / 100
        )

        p_safety_stock = (
            p_daily_demand * safety_stock_days
        )

        p_reorder_point = (
            p_daily_demand * lead_time
            + p_safety_stock
        )

        # Use entered current stock as baseline
        # for selected product and a proportional estimate
        if product == selected_product:
            p_stock = current_stock
        else:
            p_stock = current_stock

        if p_stock < p_reorder_point:
            alert = "🔴 REORDER"
        else:
            alert = "🟢 OK"

        inventory_rows.append({
            "Product": product,
            "Current Stock": round(p_stock),
            "Daily Forecast": round(p_daily_demand, 2),
            "Reorder Point": round(p_reorder_point),
            "Alert": alert
        })

    inventory_df = pd.DataFrame(inventory_rows)

    st.dataframe(
        inventory_df,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # STOCKOUT PROBABILITY
    # ========================================================

    st.markdown(
        '<div class="section-title">⚠️ Stockout Probability</div>',
        unsafe_allow_html=True
    )

    stockout_df = inventory_df.copy()

    stockout_df["Stockout Probability"] = stockout_df.apply(
        lambda row: min(
            100,
            max(
                0,
                ((row["Reorder Point"] - row["Current Stock"])
                 / max(row["Reorder Point"], 1)) * 100
            )
        ),
        axis=1
    )

    stockout_df["Stockout Probability"] = (
        stockout_df["Stockout Probability"].round(1)
    )

    fig = px.bar(
        stockout_df,
        x="Product",
        y="Stockout Probability",
        color="Stockout Probability",
        title="Estimated Stockout Risk by Product",
        labels={
            "Stockout Probability":
            "Probability (%)"
        }
    )

    fig.update_layout(
        height=400,
        plot_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # ORDER RECOMMENDATIONS
    # ========================================================

    st.markdown(
        '<div class="section-title">🛒 Order Recommendations</div>',
        unsafe_allow_html=True
    )

    recommendation_df = inventory_df.copy()

    recommendation_df["Recommended Order"] = (
        recommendation_df["Reorder Point"]
        + recommendation_df["Daily Forecast"] * 7
        - recommendation_df["Current Stock"]
    )

    recommendation_df["Recommended Order"] = (
        recommendation_df["Recommended Order"]
        .clip(lower=0)
        .round()
        .astype(int)
    )

    recommendation_df["Recommendation"] = np.where(
        recommendation_df["Recommended Order"] > 0,
        "📦 Replenish",
        "✅ No Order Required"
    )

    st.dataframe(
        recommendation_df[
            [
                "Product",
                "Current Stock",
                "Daily Forecast",
                "Reorder Point",
                "Recommended Order",
                "Recommendation"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # COST ESTIMATION
    # ========================================================

    st.markdown(
        '<div class="section-title">💰 Cost Estimation</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Ordering Cost",
            f"₹{ordering_cost:,.2f}"
        )

    with c2:
        st.metric(
            "Holding Cost",
            f"₹{estimated_holding:,.2f}"
        )

    with c3:
        st.metric(
            "Potential Stockout Cost",
            f"₹{estimated_stockout:,.2f}"
        )

    with c4:
        st.metric(
            "Total Estimated Cost",
            f"₹{estimated_total_cost:,.2f}"
        )

    # ========================================================
    # MODEL COMPARISON
    # ========================================================

    st.markdown(
        '<div class="section-title">🤖 Forecast Model Comparison</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        models,
        use_container_width=True,
        hide_index=True
    )

    mae_col = next(
        (
            c for c in models.columns
            if "mae" in c
        ),
        None
    )

    model_col = next(
        (
            c for c in models.columns
            if "model" in c or "algorithm" in c
        ),
        None
    )

    if mae_col and model_col:

        fig = px.bar(
            models,
            x=model_col,
            y=mae_col,
            color=model_col,
            text_auto=".2f",
            title="Model Comparison using MAE"
        )

        fig.update_layout(
            height=350,
            plot_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ========================================================
    # PRODUCT STATISTICS
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Product Demand Statistics</div>',
        unsafe_allow_html=True
    )

    if not product_stats.empty:

        st.dataframe(
            product_stats,
            use_container_width=True,
            hide_index=True
        )

        stat_cols = [
            "mean",
            "min",
            "max"
        ]

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
                text_auto=".2f",
                title=f"Demand Statistics — Product {selected_product}"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown("---")

    st.markdown(
        """
        <div style="text-align:center;color:#60758a;">
        <b>AI-Based Inventory and Demand Forecasting</b><br>
        Data-driven planning tool for demand prediction,
        inventory optimization and stockout prevention.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success("✅ Dashboard data loaded successfully!")

except Exception as e:

    st.error("❌ Unable to load the dashboard data.")

    st.write(
        "Please check the CSV filenames and column names."
    )

    st.write("Error:", e)
