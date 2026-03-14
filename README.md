# Campus Energy Digital Twin

A real-time digital twin system for monitoring, predicting, and optimising campus energy systems. Built for the Innothon hackathon.

---

## Features

| Feature | Description |
|---|---|
| 📡 **IoT Data Simulation** | Realistic synthetic sensor data – solar generation, campus demand, battery SoC, grid flows, temperature |
| 🤖 **AI/ML Energy Prediction** | Random Forest models predict demand and solar generation with look-ahead forecasting |
| 🚨 **Anomaly Detection** | Isolation Forest + rule-based fault detection for abnormal energy usage and equipment faults |
| ⚡ **Solar & Battery Optimizer** | Greedy dispatch optimizer that minimises grid import cost, maximises solar self-consumption |
| 📊 **Digital Twin Dashboard** | Streamlit web dashboard with real-time charts, KPIs, forecasts, and anomaly alerts |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the Digital Twin Dashboard

```bash
streamlit run src/dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 3. Run unit tests

```bash
python -m pytest tests/ -v
```

---

## Architecture

```
innothon_digital_twin/
├── requirements.txt                  # Python dependencies
├── src/
│   ├── data/
│   │   └── iot_simulator.py          # Simulates IoT sensor readings
│   ├── models/
│   │   ├── energy_predictor.py       # Random Forest demand & solar predictor
│   │   └── anomaly_detector.py       # Isolation Forest + rule-based fault detector
│   ├── optimization/
│   │   └── solar_battery_optimizer.py # Greedy solar/battery dispatch optimizer
│   └── dashboard/
│       └── app.py                    # Streamlit digital twin dashboard
└── tests/
    ├── test_iot_simulator.py
    ├── test_energy_predictor.py
    ├── test_anomaly_detector.py
    └── test_optimizer.py
```

---

## Dashboard Tabs

| Tab | Contents |
|---|---|
| 📊 **Energy Overview** | Real-time power flow chart, battery SoC, energy mix pie chart, 90-day KPIs |
| 🤖 **AI Predictions** | Model performance metrics, configurable horizon forecast chart and table |
| ⚡ **Optimizer** | Optimised vs baseline grid import, battery action distribution, hourly savings, live recommendation |
| 🚨 **Anomaly Detection** | Detected anomaly scatter plot, fault type breakdown bar chart, recent anomalies table |

---

## Modules

### `src/data/iot_simulator.py`
Generates synthetic 15-minute interval IoT data for a campus energy system including solar PV output, building load profiles (weekday/weekend), battery state-of-charge evolution, grid import/export, and randomly injected anomalies.

### `src/models/energy_predictor.py`
Trains two Random Forest regressors on historical IoT data:
- **Demand predictor** – uses time features, temperature, and lag values
- **Solar predictor** – uses irradiance, cloud cover, and lag values

Supports single-step and multi-step (horizon) forecasting. Models can be saved/loaded with `joblib`.

### `src/models/anomaly_detector.py`
Combines:
- **Isolation Forest** – unsupervised ML model for statistical outlier detection
- **Rule-based checks** – demand spikes, solar underperformance, battery overcharge/undercharge, grid overload

### `src/optimization/solar_battery_optimizer.py`
Implements a priority-stack greedy dispatch strategy:
1. Serve load from solar (free)
2. Charge battery from surplus solar
3. Export remaining surplus to grid
4. Discharge battery to cover deficit
5. Import from grid (last resort, penalised more during peak hours)

Computes economic KPIs: energy cost, cost savings vs. baseline, self-sufficiency ratio.

---

## Technology Stack

- **Python 3.12** · **pandas** · **numpy** · **scikit-learn** · **Streamlit** · **Plotly**

