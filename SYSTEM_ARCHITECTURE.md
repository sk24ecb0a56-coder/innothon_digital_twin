# System Architecture - Hardware & Software Integration

**Campus Energy Digital Twin - Complete System Overview**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CAMPUS ENERGY                           │
│                        DIGITAL TWIN SYSTEM                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   PHYSICAL   │         │  DIGITAL     │         │    USERS     │
│    LAYER     │ ──────→ │   LAYER      │ ◄────── │   & JUDGES   │
│  (Hardware)  │  Data   │ (Software)   │  View   │ (Dashboard)  │
└──────────────┘         └──────────────┘         └──────────────┘
       ↓                        ↓                        ↓
  ESP32 Sensors           AI Models + DB           Web Interface
  Solar/Battery        Predictions/Anomalies       Visualizations
  Real-time Data         Optimization              KPIs & Alerts
```

---

## Detailed Architecture Diagram

```
╔════════════════════════════════════════════════════════════════╗
║                      PHYSICAL LAYER                            ║
║                    (Hardware Components)                       ║
╚════════════════════════════════════════════════════════════════╝

┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Solar Panel  │   │ Battery Pack │   │  Campus      │
│   (0.3 kW)   │   │  (4S 14.8V)  │   │  Buildings   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │
       └──────────┬───────┴───────────────────┘
                  │
         ┌────────▼────────┐
         │  ESP32 #1       │  WiFi
         │  Sensor Node    │◄──────────┐
         │                 │           │
         │  Sensors:       │           │
         │  • ACS712       │           │
         │  • DHT22        │           │
         │  • BH1750       │           │
         │  • Voltage ADC  │           │
         │                 │           │
         │  Outputs:       │           │
         │  • 6× LEDs      │           │
         │  • Serial Log   │           │
         └─────────────────┘           │
                                       │
         ┌────────────────┐            │
         │  ESP32 #2       │  WiFi     │
         │  (Backup/Aux)   │◄──────────┘
         └─────────────────┘

╔════════════════════════════════════════════════════════════════╗
║                    COMMUNICATION LAYER                         ║
║                   (Data Transmission)                          ║
╚════════════════════════════════════════════════════════════════╝

         ESP32 Sensor Node
                │
                │ HTTP POST Request
                │ Every 15 seconds
                │
                │ JSON Payload:
                │ {
                │   "timestamp": 1234567890,
                │   "solar_gen_kw": 0.245,
                │   "battery_voltage": 14.2,
                │   "battery_soc_pct": 65.5,
                │   "temperature_c": 27.3,
                │   "demand_kw": 0.387,
                │   ...
                │ }
                │
                ▼
    ┌───────────────────────┐
    │  Flask HTTP Server    │  Port 5000
    │  (Python)             │  http://laptop:5000/api/sensor-data
    │                       │
    │  Endpoints:           │
    │  POST /api/sensor-data│  ← Receive from ESP32
    │  GET  /api/sensor-data│  ← Query latest
    │  GET  /health         │  ← Health check
    └───────────┬───────────┘
                │
                ▼
         ┌──────────────┐
         │  JSON File   │  live_sensor_data.json
         │  (Temporary) │  (last reading only)
         └──────────────┘

╔════════════════════════════════════════════════════════════════╗
║                      DATA LAYER (NEW!)                         ║
║                   (Persistent Storage)                         ║
╚════════════════════════════════════════════════════════════════╝

         ┌─────────────────────────────────┐
         │   SQLite Database               │
         │   sensor_data.db                │
         │                                 │
         │   Tables:                       │
         │   • sensor_readings             │
         │   • predictions                 │
         │   • anomalies                   │
         │   • optimization_results        │
         │                                 │
         │   Retention: 90 days            │
         │   Size: ~50MB                   │
         └─────────────────────────────────┘

         Schema:

         sensor_readings:
         ┌──────────────┬──────────────┬─────────┐
         │ id (PK)      │ timestamp    │ solar_  │
         │              │              │ gen_kw  │
         ├──────────────┼──────────────┼─────────┤
         │ 1            │ 2026-03-20   │ 0.245   │
         │ 2            │ 2026-03-20   │ 0.251   │
         └──────────────┴──────────────┴─────────┘

         Columns (15 total):
         - id, timestamp, solar_gen_kw, solar_voltage
         - solar_current, battery_voltage, battery_soc_pct
         - temperature_c, irradiance_lux, demand_kw
         - grid_import_kw, grid_export_kw
         - is_anomaly, anomaly_score, anomaly_type

╔════════════════════════════════════════════════════════════════╗
║                     PROCESSING LAYER                           ║
║                    (AI & Optimization)                         ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│                    ML MODEL PIPELINE                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Data Ingestion
         │
         │ Load from SQLite DB
         │ OR generate synthetic data
         │
         ▼
    pandas DataFrame
    (90 days × 96 readings/day = 8,640 rows)
         │
         ▼
Step 2: Feature Engineering
         │
         │ Add lag features:
         │ • demand_kw_lag1 (previous 15-min)
         │ • demand_kw_lag4 (previous 1-hour)
         │ • demand_kw_rolling_mean (4-period avg)
         │ • solar_gen_kw_lag1
         │
         ▼
Step 3: Model Training (AUTOMATIC)
         │
         ├─────────────────────┬──────────────────────┐
         │                     │                      │
         ▼                     ▼                      ▼
    ┌─────────┐         ┌─────────┐          ┌─────────┐
    │ Demand  │         │ Solar   │          │Anomaly  │
    │ Model   │         │ Model   │          │Detector │
    │         │         │         │          │         │
    │ Random  │         │ Random  │          │Isolation│
    │ Forest  │         │ Forest  │          │ Forest  │
    │         │         │         │          │         │
    │ 8 feat. │         │ 6 feat. │          │ 7 feat. │
    │ 100 tree│         │ 100 tree│          │ 5% cont.│
    └────┬────┘         └────┬────┘          └────┬────┘
         │                   │                     │
         │ Predicts:         │ Predicts:           │ Detects:
         │ • Next demand     │ • Next solar        │ • Anomalies
         │ • 4-24h horizon   │ • 4-24h horizon     │ • Fault types
         │                   │                     │
         └───────────────────┴─────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Trained Models │
                    │  (in memory)    │
                    │                 │
                    │  Optional:      │
                    │  Save to disk   │
                    │  .joblib files  │
                    └─────────────────┘

Step 4: Optimization Engine
         │
         ▼
    ┌──────────────────────────────────┐
    │  Solar Battery Optimizer         │
    │                                  │
    │  Inputs:                         │
    │  • Predicted demand              │
    │  • Predicted solar               │
    │  • Current battery SoC           │
    │  • Tariff structure              │
    │                                  │
    │  Algorithm (Greedy Dispatch):    │
    │  1. Serve load from solar        │
    │  2. Charge battery if surplus    │
    │  3. Export to grid               │
    │  4. Discharge battery if deficit │
    │  5. Import from grid (last)      │
    │                                  │
    │  Outputs:                        │
    │  • Optimal battery schedule      │
    │  • Grid import/export plan       │
    │  • Cost savings (₹)              │
    │  • Self-sufficiency (%)          │
    └──────────────────────────────────┘

╔════════════════════════════════════════════════════════════════╗
║                   PRESENTATION LAYER                           ║
║                   (User Interface)                             ║
╚════════════════════════════════════════════════════════════════╝

         ┌────────────────────────────────┐
         │  Streamlit Web Dashboard       │  Port 8501
         │  http://localhost:8501         │
         │                                │
         │  Components:                   │
         │                                │
         │  📊 Tab 1: Energy Overview     │
         │     • Real-time power flow     │
         │     • Battery SoC gauge        │
         │     • 24h history chart        │
         │     • Energy mix pie chart     │
         │                                │
         │  🤖 Tab 2: AI Predictions      │
         │     • Model performance        │
         │     • 4-24h forecast plots     │
         │     • Accuracy metrics         │
         │                                │
         │  ⚡ Tab 3: Optimizer            │
         │     • Baseline vs optimized    │
         │     • Cost savings breakdown   │
         │     • Battery schedule         │
         │                                │
         │  🚨 Tab 4: Anomaly Detection   │
         │     • Recent alerts            │
         │     • Fault type breakdown     │
         │     • Anomaly scatter plot     │
         │                                │
         │  Sidebar:                      │
         │     • Historical data range    │
         │     • System capacity config   │
         │     • Tariff settings          │
         │     • Auto-refresh toggle      │
         └────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Judge/User    │
              │  Web Browser   │
              │                │
              │  • Laptop      │
              │  • Projector   │
              │  • Mobile      │
              └────────────────┘

╔════════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT VIEW                             ║
║               (How Everything Runs)                            ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│                    Your Laptop                              │
│                                                             │
│  Terminal 1:                                                │
│  $ python hardware/esp32_data_receiver.py                   │
│    → Flask server running on port 5000                      │
│    → Receives data from ESP32                               │
│    → Saves to database                                      │
│                                                             │
│  Terminal 2:                                                │
│  $ streamlit run src/dashboard/app.py                       │
│    → Web server on port 8501                                │
│    → Reads from database                                    │
│    → Trains ML models on startup                            │
│    → Serves dashboard to browser                            │
│                                                             │
│  Browser:                                                   │
│  http://localhost:8501                                      │
│    → Display to judges                                      │
│                                                             │
│  Database:                                                  │
│  sensor_data.db                                             │
│    → SQLite file in project root                            │
│    → Stores all historical data                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   WiFi Network                              │
│   (Both laptop and ESP32 connected to same network)        │
│                                                             │
│   Laptop IP: 192.168.1.100 (example)                       │
│   ESP32 IP: 192.168.1.101 (auto-assigned)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ESP32 Hardware                           │
│                                                             │
│  Power: Battery pack (4S 14.8V) → Buck converter (5V)      │
│  WiFi: Connected to your hotspot                           │
│  Sensors: Reading every 15 seconds                         │
│  LEDs: Visual feedback                                     │
│  HTTP: Posting JSON to laptop:5000                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Sequence

### Real-Time Operation (15-second cycle)

```
Time T=0s: ESP32 reads sensors
         │
         ├─ GPIO34: Solar voltage → 8.3V
         ├─ GPIO35: Solar current → 0.03A
         ├─ GPIO32: Battery voltage → 14.2V
         ├─ GPIO4:  Temperature → 27.3°C
         ├─ I2C:    Irradiance → 45230 lux
         └─ Compute: Demand, SoC, etc.
         │
Time T=1s: Format JSON payload
         │
         {
           "timestamp": 1234567890,
           "solar_gen_kw": 0.245,
           "battery_voltage": 14.2,
           "battery_soc_pct": 65.5,
           ...
         }
         │
Time T=2s: HTTP POST to server
         │
         POST http://192.168.1.100:5000/api/sensor-data
         Content-Type: application/json
         │
         ▼
Time T=2.5s: Flask server receives
         │
         ├─ Validate JSON
         ├─ Save to SQLite database (INSERT)
         └─ Return 200 OK
         │
Time T=3s: Dashboard auto-refresh (if enabled)
         │
         ├─ Query latest from database
         ├─ Update live metrics
         ├─ Run anomaly detection on new reading
         └─ Re-render UI
         │
Time T=15s: Cycle repeats
```

---

## ML Model Training Flow

### When Models Are Trained

**Trigger Events:**
1. Dashboard startup (first run)
2. User changes historical data range slider
3. User changes system capacity (solar/battery)
4. Manual refresh button click

**Training Process:**

```
Step 1: Data Generation/Loading
        │
        ├─ Option A: Generate synthetic data
        │   └─ generate_iot_data(days=90)
        │       • Creates 8,640 rows (90 × 96)
        │       • Realistic solar/demand profiles
        │       • Injects 1% anomalies
        │
        └─ Option B: Load from database (NEW!)
            └─ SELECT * FROM sensor_readings
                WHERE timestamp > (NOW() - 90 days)
        │
        ▼
Step 2: Feature Engineering (~1 second)
        │
        • Add lag features
        • Compute rolling averages
        • Create time-based features
        │
        ▼
Step 3: Train Demand Model (~3 seconds)
        │
        • Split 80/20 train/test
        • Fit RandomForest (100 trees)
        • Evaluate on test set
        • Store R² and MAE metrics
        │
        ▼
Step 4: Train Solar Model (~3 seconds)
        │
        • Split 80/20 train/test
        • Fit RandomForest (100 trees)
        • Evaluate on test set
        • Store R² and MAE metrics
        │
        ▼
Step 5: Train Anomaly Detector (~2 seconds)
        │
        • Fit IsolationForest
        • Compute anomaly threshold
        • Combine with rule-based detector
        │
        ▼
Step 6: Run Optimizer (~2 seconds)
        │
        • Simulate battery dispatch
        • Calculate KPIs
        • Generate optimized schedule
        │
        ▼
Step 7: Cache in Session State
        │
        • Store models in st.session_state
        • Store results in st.session_state
        • Display dashboard
        │
Total time: ~11 seconds for 90 days of data
```

**Model Performance (Expected):**

| Model | Algorithm | Features | R² Score | MAE |
|-------|-----------|----------|----------|-----|
| Demand Predictor | Random Forest | 8 | >0.70 | <80 kW |
| Solar Predictor | Random Forest | 6 | >0.70 | <80 kW |
| Anomaly Detector | Isolation Forest | 7 | N/A | 99% detection |

**Where Models Are Stored:**

- **During Session:** In Streamlit session_state (RAM)
- **Between Sessions:** Can be saved to disk with joblib
- **For Demo:** Fresh training on startup (shows live learning!)

---

## Database Schema (NEW!)

### Table: sensor_readings

```sql
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    solar_gen_kw REAL NOT NULL,
    solar_voltage REAL,
    solar_current REAL,
    battery_voltage REAL NOT NULL,
    battery_soc_pct REAL NOT NULL,
    temperature_c REAL NOT NULL,
    irradiance_lux REAL,
    irradiance_norm REAL,
    demand_kw REAL NOT NULL,
    grid_import_kw REAL,
    grid_export_kw REAL,
    is_anomaly INTEGER DEFAULT 0,
    anomaly_score REAL,
    anomaly_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_anomaly ON sensor_readings(is_anomaly);
```

### Table: predictions (Optional)

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    prediction_horizon_hours INTEGER NOT NULL,
    predicted_demand_kw REAL NOT NULL,
    predicted_solar_kw REAL NOT NULL,
    actual_demand_kw REAL,
    actual_solar_kw REAL,
    demand_error REAL,
    solar_error REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Query Examples

**Get last 24 hours of data:**
```sql
SELECT * FROM sensor_readings
WHERE timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;
```

**Get anomalies in last week:**
```sql
SELECT timestamp, anomaly_type, anomaly_score
FROM sensor_readings
WHERE is_anomaly = 1
  AND timestamp > datetime('now', '-7 days')
ORDER BY anomaly_score DESC;
```

**Calculate average daily solar generation:**
```sql
SELECT DATE(timestamp) as date,
       AVG(solar_gen_kw) as avg_solar,
       MAX(solar_gen_kw) as peak_solar
FROM sensor_readings
WHERE timestamp > datetime('now', '-30 days')
GROUP BY DATE(timestamp);
```

---

## Performance Metrics

### System Capacity

| Component | Value | Unit |
|-----------|-------|------|
| Solar Capacity | 300 | kW |
| Battery Capacity | 500 | kWh |
| Battery Efficiency | 95 | % |
| Max Charge Rate | 100 | kW |
| Max Discharge Rate | 100 | kW |
| SoC Operating Window | 10-95 | % |

### Typical Operation

| Metric | Daytime | Nighttime |
|--------|---------|-----------|
| Solar Generation | 50-250 kW | 0 kW |
| Campus Demand | 150-300 kW | 80-120 kW |
| Battery SoC | 60-90% | 40-60% |
| Grid Import | 0-50 kW | 80-120 kW |
| Grid Export | 0-100 kW | 0 kW |

### Economic Results (90-day simulation)

| KPI | Value |
|-----|-------|
| Self-Sufficiency | 65-75% |
| Solar Fraction | 55-65% |
| Cost Savings | ₹50,000-80,000 |
| ROI Period | 4-6 years |
| CO₂ Reduction | 50-60 tons/year |

---

## Technology Stack

### Hardware
- **Microcontroller:** ESP32 WROOM (Xtensa dual-core 240 MHz)
- **Sensors:** DHT22, BH1750, ACS712, Voltage dividers
- **Power:** 4S Li-Ion (14.8V), LM2596 buck converter
- **Communication:** WiFi 802.11 b/g/n

### Backend
- **Language:** Python 3.12+
- **Web Framework:** Flask 3.0 (HTTP server)
- **Database:** SQLite 3 (file-based)
- **ML Library:** scikit-learn 1.4.2
- **Data Processing:** pandas 2.2.2, numpy 1.26.4

### Frontend
- **Framework:** Streamlit 1.35.0
- **Visualization:** Plotly 5.22.0
- **UI Components:** Native Streamlit widgets

### ML Models
- **Demand Forecasting:** RandomForestRegressor (100 trees)
- **Solar Forecasting:** RandomForestRegressor (100 trees)
- **Anomaly Detection:** IsolationForest (5% contamination)
- **Optimization:** Custom greedy dispatch algorithm

---

## Scalability Considerations

### Current Demo Setup
- ✅ Single ESP32 sensor node
- ✅ SQLite database (sufficient for 90 days)
- ✅ Single-user dashboard
- ✅ Local execution on laptop

### Production Scaling Path

**Phase 1: Campus Pilot (10 buildings)**
- Add 10 ESP32 nodes (one per building)
- Upgrade to PostgreSQL or TimescaleDB
- Deploy on cloud (AWS/Azure)
- Multi-user authentication

**Phase 2: Multi-Campus (100s of buildings)**
- MQTT broker for sensor data
- InfluxDB for time-series data
- Docker/Kubernetes deployment
- Load balancer + Redis cache
- Horizontal scaling of ML inference

**Phase 3: Smart City (1000s of buildings)**
- Apache Kafka for data streaming
- Spark for distributed ML training
- Microservices architecture
- Real-time anomaly alerts (SMS/email)
- API gateway for 3rd party integration

---

## Security Considerations

### Current Demo (Minimal Security)
- ⚠️ No authentication
- ⚠️ WiFi credentials in code
- ⚠️ HTTP (not HTTPS)
- ⚠️ No data encryption

### Production Requirements
- ✅ HTTPS with TLS certificates
- ✅ JWT-based authentication
- ✅ Encrypted WiFi credentials (ESP32 secure storage)
- ✅ Database encryption at rest
- ✅ Rate limiting on API endpoints
- ✅ Input validation and sanitization
- ✅ Regular security audits

---

## Monitoring & Alerting (Future)

### Health Checks
- ESP32 heartbeat every 15s
- Flask server /health endpoint
- Database connection pool monitoring
- ML model prediction latency

### Alert Triggers
- Battery SoC < 10% (critical)
- Solar underperformance > 50% (warning)
- Demand spike > 2× average (anomaly)
- ESP32 offline > 2 minutes (error)
- Grid import cost > threshold (economic)

### Logging
- Sensor data: SQLite database
- Application logs: Python logging module
- Error tracking: Console output (demo)
- Performance metrics: In-memory (demo)

---

## Development Workflow

### Local Development
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Connect ESP32 via USB
4. Upload firmware via Arduino IDE
5. Get laptop IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
6. Update ESP32 code with laptop IP
7. Power ESP32 from battery/USB
8. Run Flask server: `python hardware/esp32_data_receiver.py`
9. Run dashboard: `streamlit run src/dashboard/app.py`
10. Open browser: `http://localhost:8501`

### Testing
- Unit tests: `pytest tests/`
- Hardware test: Serial monitor (Arduino IDE)
- API test: `curl http://localhost:5000/health`
- Integration test: Check dashboard updates with live data

### Deployment (Demo Day)
1. Charge batteries fully (night before)
2. Test all components individually
3. Assemble on demo table
4. Connect to venue WiFi (or mobile hotspot)
5. Start Flask server on laptop
6. Start Streamlit dashboard
7. Power on ESP32 hardware
8. Verify data flow (check serial monitor + dashboard)
9. Prepare presentation
10. Win hackathon! 🏆

---

## Questions & Answers

**Q: Do the ML models need internet to work?**
A: No! Everything runs locally on your laptop. No cloud required.

**Q: How long does training take?**
A: ~10-15 seconds for 90 days of data. Fast enough for live demo!

**Q: Can we demo without hardware?**
A: Yes! Dashboard works with simulated data. But hardware is more impressive.

**Q: What if WiFi fails during demo?**
A: Use mobile hotspot. Or demo with simulated data only.

**Q: How do we show the ML "learning"?**
A: Adjust sliders in dashboard → models retrain instantly → show updated predictions!

**Q: Is this production-ready?**
A: For demo: YES. For real deployment: needs auth, HTTPS, monitoring, etc.

**Q: Can judges interact with it?**
A: Yes! They can adjust sliders, change tariffs, see predictions update live.

---

## Next Steps

1. ✅ Review this architecture document
2. ✅ Build hardware using HARDWARE_BUILD_GUIDE.md
3. ✅ Test each component individually
4. ✅ Integrate and test end-to-end
5. ✅ Prepare demo presentation
6. ✅ Practice explaining architecture to judges
7. ✅ Have backup plan (simulated data if hardware fails)

---

**This architecture is designed to impress judges while being hackathon-feasible!** 🚀

Key selling points:
- ✅ Real hardware integration (IoT)
- ✅ Live ML training (AI)
- ✅ Battery optimization (Smart algorithms)
- ✅ Interactive dashboard (UX)
- ✅ Economic + environmental impact (Value proposition)
- ✅ Scalable design (Future-proof)

Good luck! 🏆
