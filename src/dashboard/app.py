"""
Campus Energy Digital Twin Dashboard.

Real-time monitoring and visualisation of campus energy systems using
Streamlit and Plotly.

Run with:
    streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import sys
import os
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.iot_simulator import generate_iot_data, get_live_reading
from src.models.energy_predictor import EnergyPredictor
from src.models.anomaly_detector import AnomalyDetector
from src.optimization.solar_battery_optimizer import SolarBatteryOptimizer, SystemConfig

AUTO_REFRESH_INTERVAL_SECONDS = 10


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Campus Energy Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
st.sidebar.title("⚡ Digital Twin Controls")
st.sidebar.markdown("---")

days_history = st.sidebar.slider("Historical data (days)", 30, 180, 90, step=30)
solar_capacity = st.sidebar.slider("Solar capacity (kW)", 50, 600, 300, step=50)
battery_capacity = st.sidebar.slider("Battery capacity (kWh)", 100, 1000, 500, step=100)
auto_refresh = st.sidebar.checkbox(f"Auto-refresh ({AUTO_REFRESH_INTERVAL_SECONDS} s)", value=False)
refresh_clicked = st.sidebar.button("🔄 Refresh now")

st.sidebar.markdown("---")
st.sidebar.markdown("**Tariff Settings**")
peak_tariff = st.sidebar.number_input("Peak tariff (INR/kWh)", 5.0, 20.0, 12.0, step=0.5)
offpeak_tariff = st.sidebar.number_input("Off-peak tariff (INR/kWh)", 2.0, 15.0, 8.0, step=0.5)

# ---------------------------------------------------------------------------
# Session state: train models once per session or when params change
# ---------------------------------------------------------------------------
cache_key = (days_history, solar_capacity, battery_capacity)

if "cache_key" not in st.session_state or st.session_state.cache_key != cache_key:
    st.session_state.cache_key = cache_key

    with st.spinner("⚙️ Generating historical IoT data and training AI models…"):
        config = SystemConfig(
            solar_capacity_kw=float(solar_capacity),
            battery_capacity_kwh=float(battery_capacity),
            grid_import_cost_per_kwh=offpeak_tariff,
            peak_hours=(9, 18),
            peak_tariff_multiplier=peak_tariff / offpeak_tariff,
        )

        hist_df = generate_iot_data(days=days_history, solar_capacity_kw=solar_capacity)

        predictor = EnergyPredictor()
        predictor.fit(hist_df)

        detector = AnomalyDetector()
        detector.fit(hist_df)

        optimizer = SolarBatteryOptimizer(config=config)
        sim_df = optimizer.run_simulation(hist_df)
        sim_df = detector.predict(sim_df)

        kpis = optimizer.get_kpis(sim_df)

        st.session_state.hist_df = hist_df
        st.session_state.sim_df = sim_df
        st.session_state.predictor = predictor
        st.session_state.detector = detector
        st.session_state.optimizer = optimizer
        st.session_state.kpis = kpis
        st.session_state.config = config

hist_df: pd.DataFrame = st.session_state.hist_df
sim_df: pd.DataFrame = st.session_state.sim_df
predictor: EnergyPredictor = st.session_state.predictor
detector: AnomalyDetector = st.session_state.detector
optimizer: SolarBatteryOptimizer = st.session_state.optimizer
kpis: dict = st.session_state.kpis

# ---------------------------------------------------------------------------
# Live reading
# ---------------------------------------------------------------------------
live = get_live_reading(solar_capacity_kw=float(solar_capacity))
battery_soc_pct = sim_df["opt_battery_soc_pct"].iloc[-1]

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("🏫 Campus Energy Digital Twin")
st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# ---------------------------------------------------------------------------
# KPI Row
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("☀️ Solar Gen (kW)", f"{live['solar_gen_kw']:.1f}")
k2.metric("🏢 Campus Demand (kW)", f"{live['demand_kw']:.1f}")
k3.metric("🔋 Battery SoC", f"{battery_soc_pct:.1f} %")
k4.metric("🌐 Grid Import (kW)", f"{live['grid_import_kw']:.1f}")
k5.metric("💡 Self-Sufficiency", f"{kpis['self_sufficiency_pct']:.1f} %")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Energy Overview", "🤖 AI Predictions", "⚡ Optimizer", "🚨 Anomaly Detection"]
)

# ============================================================
# TAB 1 – Energy Overview
# ============================================================
with tab1:
    st.subheader("Real-Time Energy Flow")

    last_day = sim_df.tail(96)  # last 24 h (96 × 15-min intervals)

    fig_flow = go.Figure()
    fig_flow.add_trace(go.Scatter(
        x=last_day["timestamp"], y=last_day["solar_gen_kw"],
        name="Solar Generation", fill="tozeroy", line=dict(color="#FFC300"),
    ))
    fig_flow.add_trace(go.Scatter(
        x=last_day["timestamp"], y=last_day["demand_kw"],
        name="Campus Demand", line=dict(color="#E74C3C", width=2),
    ))
    fig_flow.add_trace(go.Scatter(
        x=last_day["timestamp"], y=last_day["opt_grid_import_kw"],
        name="Grid Import", line=dict(color="#3498DB", dash="dot"),
    ))
    fig_flow.update_layout(
        xaxis_title="Time", yaxis_title="Power (kW)",
        legend=dict(orientation="h"), height=350,
    )
    st.plotly_chart(fig_flow, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Battery State of Charge (last 24 h)")
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(
            x=last_day["timestamp"], y=last_day["opt_battery_soc_pct"],
            fill="tozeroy", name="Battery SoC (%)", line=dict(color="#27AE60"),
        ))
        fig_soc.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Min SoC")
        fig_soc.add_hline(y=95, line_dash="dash", line_color="orange", annotation_text="Max SoC")
        fig_soc.update_layout(yaxis=dict(range=[0, 100]), yaxis_title="SoC (%)", height=280)
        st.plotly_chart(fig_soc, use_container_width=True)

    with col_b:
        st.subheader("Energy Mix (90-day summary)")
        pie_labels = ["Solar Self-consumed", "Grid Import"]
        solar_self = kpis["total_solar_kwh"] - kpis["total_grid_export_kwh"]
        pie_values = [max(solar_self, 0), kpis["total_grid_import_kwh"]]
        fig_pie = px.pie(
            names=pie_labels, values=pie_values,
            color_discrete_sequence=["#FFC300", "#3498DB"],
        )
        fig_pie.update_layout(height=280)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📋 System KPIs (90-day)")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("Total Solar (MWh)", f"{kpis['total_solar_kwh']/1000:.1f}")
    kpi_col2.metric("Total Demand (MWh)", f"{kpis['total_demand_kwh']/1000:.1f}")
    kpi_col3.metric("Grid Export (MWh)", f"{kpis['total_grid_export_kwh']/1000:.1f}")
    kpi_col4.metric("Cost Savings (INR)", f"₹{kpis['total_cost_savings_inr']:,.0f}")

# ============================================================
# TAB 2 – AI Predictions
# ============================================================
with tab2:
    st.subheader("AI-Powered Energy Forecasting")

    st.markdown("**Model Performance**")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Demand MAE (kW)", f"{predictor.metrics.get('demand_mae', 0):.1f}")
    m2.metric("Demand R²", f"{predictor.metrics.get('demand_r2', 0):.3f}")
    m3.metric("Solar MAE (kW)", f"{predictor.metrics.get('solar_mae', 0):.1f}")
    m4.metric("Solar R²", f"{predictor.metrics.get('solar_r2', 0):.3f}")

    horizon = st.slider("Forecast horizon (steps × 15 min)", 4, 24, 8)
    current_row = hist_df.iloc[-1].copy()
    forecast_df = predictor.predict_horizon(current_row, horizon_steps=horizon)
    now = datetime.now()
    forecast_df["time"] = [now + timedelta(minutes=15 * i) for i in range(1, len(forecast_df) + 1)]

    fig_pred = go.Figure()
    fig_pred.add_trace(go.Scatter(
        x=forecast_df["time"], y=forecast_df["predicted_demand_kw"],
        name="Predicted Demand", line=dict(color="#E74C3C", width=2),
    ))
    fig_pred.add_trace(go.Scatter(
        x=forecast_df["time"], y=forecast_df["predicted_solar_kw"],
        name="Predicted Solar", line=dict(color="#FFC300", width=2),
    ))
    fig_pred.update_layout(
        xaxis_title="Time", yaxis_title="Power (kW)",
        legend=dict(orientation="h"), height=350,
    )
    st.plotly_chart(fig_pred, use_container_width=True)

    st.subheader("📋 Forecast Table")
    st.dataframe(
        forecast_df[["time", "predicted_demand_kw", "predicted_solar_kw"]]
        .rename(columns={"time": "Time", "predicted_demand_kw": "Demand (kW)", "predicted_solar_kw": "Solar (kW)"})
        .set_index("Time"),
        use_container_width=True,
    )

# ============================================================
# TAB 3 – Optimizer
# ============================================================
with tab3:
    st.subheader("Solar & Battery Optimizer")

    last_week = sim_df.tail(7 * 96)

    fig_opt = go.Figure()
    fig_opt.add_trace(go.Scatter(
        x=last_week["timestamp"], y=last_week["opt_grid_import_kw"],
        name="Optimised Grid Import", line=dict(color="#3498DB"),
    ))
    fig_opt.add_trace(go.Scatter(
        x=last_week["timestamp"], y=last_week["grid_import_kw"],
        name="Baseline Grid Import", line=dict(color="#BDC3C7", dash="dash"),
    ))
    fig_opt.update_layout(
        xaxis_title="Time", yaxis_title="Grid Import (kW)",
        legend=dict(orientation="h"), height=300,
    )
    st.plotly_chart(fig_opt, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Battery Action Distribution (last 7 days)")
        action_counts = last_week["opt_battery_action"].value_counts().reset_index()
        action_counts.columns = ["Action", "Count"]
        fig_bar = px.bar(
            action_counts, x="Action", y="Count",
            color="Action",
            color_discrete_map={"charge": "#27AE60", "discharge": "#E74C3C", "idle": "#95A5A6"},
        )
        fig_bar.update_layout(height=280, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Hourly Cost Savings (last 7 days)")
        last_week_h = last_week.copy()
        last_week_h["hour_label"] = last_week_h["timestamp"].dt.strftime("%H:00")
        hourly_savings = last_week_h.groupby("hour_label")["opt_cost_savings_inr"].mean().reset_index()
        fig_savings = px.bar(
            hourly_savings, x="hour_label", y="opt_cost_savings_inr",
            labels={"hour_label": "Hour", "opt_cost_savings_inr": "Avg Savings (INR)"},
            color_discrete_sequence=["#27AE60"],
        )
        fig_savings.update_layout(height=280)
        st.plotly_chart(fig_savings, use_container_width=True)

    st.subheader("🔍 Current Optimizer Recommendation")
    current_result = optimizer.step(
        solar_gen_kw=live["solar_gen_kw"],
        demand_kw=live["demand_kw"],
        battery_soc_kwh=battery_soc_pct / 100 * battery_capacity,
        hour=datetime.now().hour + datetime.now().minute / 60,
    )
    st.info(f"**Action:** `{current_result.battery_action.value.upper()}` — {current_result.recommendation}")
    r1, r2, r3 = st.columns(3)
    r1.metric("Battery Power (kW)", f"{current_result.battery_power_kw:+.1f}")
    r2.metric("Grid Import (kW)", f"{current_result.grid_import_kw:.1f}")
    r3.metric("Est. Cost Savings (INR)", f"₹{current_result.cost_savings_inr:.2f}")

# ============================================================
# TAB 4 – Anomaly Detection
# ============================================================
with tab4:
    st.subheader("Anomaly Detection & Fault Analysis")

    anomaly_df = sim_df[sim_df["is_anomaly_any"] == 1].copy()
    normal_count = len(sim_df) - len(anomaly_df)

    col_an1, col_an2, col_an3 = st.columns(3)
    col_an1.metric("Total Readings", f"{len(sim_df):,}")
    col_an2.metric("Anomalies Detected", f"{len(anomaly_df):,}")
    col_an3.metric("Anomaly Rate", f"{len(anomaly_df)/len(sim_df)*100:.2f} %")

    fig_an = go.Figure()
    fig_an.add_trace(go.Scatter(
        x=sim_df["timestamp"], y=sim_df["demand_kw"],
        mode="lines", name="Demand (kW)", line=dict(color="#BDC3C7", width=1),
    ))
    if len(anomaly_df) > 0:
        fig_an.add_trace(go.Scatter(
            x=anomaly_df["timestamp"], y=anomaly_df["demand_kw"],
            mode="markers", name="Anomaly",
            marker=dict(color="#E74C3C", size=8, symbol="x"),
        ))
    fig_an.update_layout(
        xaxis_title="Time", yaxis_title="Demand (kW)",
        legend=dict(orientation="h"), height=350,
    )
    st.plotly_chart(fig_an, use_container_width=True)

    # Fault type breakdown
    if len(anomaly_df) > 0:
        st.subheader("Fault Type Breakdown")
        all_flags: list[str] = []
        for flags in anomaly_df["fault_flags"]:
            if flags:
                all_flags.extend(flags.split(","))
        if all_flags:
            fault_series = pd.Series(all_flags).value_counts().reset_index()
            fault_series.columns = ["Fault Type", "Count"]
            fig_fault = px.bar(
                fault_series, x="Fault Type", y="Count",
                color_discrete_sequence=["#E74C3C"],
            )
            fig_fault.update_layout(height=280)
            st.plotly_chart(fig_fault, use_container_width=True)

        st.subheader("Recent Anomalies")
        display_cols = ["timestamp", "demand_kw", "solar_gen_kw", "battery_soc_pct",
                        "anomaly_score", "is_ml_anomaly", "fault_flags"]
        available = [c for c in display_cols if c in anomaly_df.columns]
        st.dataframe(
            anomaly_df[available].tail(20).reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.success("✅ No anomalies detected in the selected period.")

# ---------------------------------------------------------------------------
# Auto-refresh
# ---------------------------------------------------------------------------
if auto_refresh:
    time.sleep(AUTO_REFRESH_INTERVAL_SECONDS)
    st.rerun()
