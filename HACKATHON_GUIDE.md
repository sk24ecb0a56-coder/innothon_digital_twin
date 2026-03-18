# 🏆 2-Day Hackathon Strategy Guide: Campus Energy Digital Twin

**Team Size:** 5 members
**Duration:** Saturday-Sunday (2 full days)
**Goal:** Win the hackathon with a working campus energy digital twin prototype

---

## 📋 Table of Contents
1. [Day-by-Day Strategy](#day-by-day-strategy)
2. [Team Role Assignment](#team-role-assignment)
3. [Hardware Requirements & Cost](#hardware-requirements--cost)
4. [Circuit Diagrams](#circuit-diagrams)
5. [Physical Setup Options](#physical-setup-options)
6. [Training Data & Model Development](#training-data--model-development)
7. [FPGA Integration (Optional)](#fpga-integration-optional)
8. [Testing Checklist](#testing-checklist)
9. [Presentation Strategy](#presentation-strategy)
10. [Emergency Backup Plan](#emergency-backup-plan)

---

## 🎯 Day-by-Day Strategy

### **SATURDAY (Day 1) - Foundation & Hardware**

#### Morning (9:00 AM - 12:00 PM)
- **9:00-9:30**: Team assembly, role assignment, repository setup
- **9:30-10:30**: Test existing software (dashboard, models) - confirm everything works
- **10:30-12:00**: Hardware assembly and circuit testing

#### Afternoon (12:00 PM - 6:00 PM)
- **12:00-1:00**: Lunch + review progress
- **1:00-3:00**: ESP32 firmware development and sensor integration
- **3:00-4:30**: Connect hardware to dashboard (live data ingestion)
- **4:30-6:00**: Build physical prototype/model and mount hardware

#### Evening (6:00 PM - 9:00 PM)
- **6:00-7:00**: Dinner
- **7:00-8:30**: Test end-to-end system with live hardware data
- **8:30-9:00**: Day 1 review, identify blockers for Day 2

---

### **SUNDAY (Day 2) - Integration & Presentation**

#### Morning (9:00 AM - 12:00 PM)
- **9:00-10:00**: Fix any issues from Day 1
- **10:00-11:30**: Add FPGA integration (if available) OR enhance visualizations
- **11:30-12:00**: Final system testing

#### Afternoon (12:00 PM - 6:00 PM)
- **12:00-1:00**: Lunch + prep presentation outline
- **1:00-3:00**: Create presentation slides and demo video
- **3:00-5:00**: Practice presentation (2-3 dry runs)
- **5:00-6:00**: Final polish, backup demos, contingency plans

#### Evening (6:00 PM onwards)
- **Final Presentation & Demo**

---

## 👥 Team Role Assignment (5 Members)

### **Member 1: Software Lead** ⭐
- Manage existing codebase (Python, dashboard)
- Integrate ESP32 data streams into the dashboard
- Handle model retraining with live data
- **Skills needed**: Python, Streamlit, pandas, scikit-learn

### **Member 2: Hardware Lead** 🔧
- Assemble circuits, connect sensors
- Test voltage levels, sensor readings
- Build physical prototype structure
- **Skills needed**: Electronics, soldering, multimeter usage

### **Member 3: Firmware Developer** 💻
- Write ESP32 firmware (Arduino/MicroPython)
- Implement MQTT/HTTP data transmission
- Debug sensor communication
- **Skills needed**: C++/Arduino or MicroPython, IoT protocols

### **Member 4: Data & ML Specialist** 🤖
- Prepare training data
- Fine-tune ML models
- Validate model accuracy
- **Skills needed**: Python, scikit-learn, data analysis

### **Member 5: Presentation & Documentation** 🎤
- Create slides and demo video
- Document the system architecture
- Practice presentation delivery
- Manage time during demo
- **Skills needed**: Communication, PowerPoint/Canva, storytelling

**Note:** All members help with physical prototype assembly and presentation practice.

---

## 💰 Hardware Requirements & Cost (Minimal Budget)

### **Option A: Full Hardware Prototype (₹4,500 - ₹6,000)**

| Component | Quantity | Unit Price (INR) | Total (INR) | Purpose |
|-----------|----------|------------------|-------------|---------|
| **ESP32 DevKit** | 2 | 350 | 700 | Main microcontrollers for IoT |
| **Solar Panel (5-10W)** | 1 | 400-600 | 500 | Demonstrate solar generation |
| **Voltage Sensor** | 2 | 100 | 200 | Measure solar voltage & battery |
| **Current Sensor (ACS712 5A)** | 2 | 80 | 160 | Measure solar/battery current |
| **Temperature Sensor (DHT22)** | 1 | 180 | 180 | Ambient temperature |
| **Light Sensor (LDR or BH1750)** | 1 | 50 | 50 | Measure solar irradiance |
| **18650 Li-Ion Batteries** | 4 | 150 | 600 | Battery pack (3.7V × 4 = 14.8V) |
| **Battery Holder (4-cell)** | 1 | 100 | 100 | Hold batteries safely |
| **TP4056 Charging Module** | 2 | 30 | 60 | Battery charging circuit |
| **DC-DC Buck Converter** | 2 | 80 | 160 | Voltage regulation |
| **LEDs (white, red, green)** | 10 | 5 | 50 | Indicate building loads |
| **Resistors (220Ω, 10kΩ)** | 20 | 1 | 20 | LED current limiting |
| **Breadboard** | 2 | 50 | 100 | Quick prototyping |
| **Jumper Wires** | 1 pack | 50 | 50 | Connections |
| **Relay Module (2-channel)** | 1 | 80 | 80 | Switch loads on/off |
| **Cardboard/Acrylic Base** | 1 | 200 | 200 | Physical structure |
| **Glue Gun, Tape, Markers** | - | 150 | 150 | Assembly materials |
| **WiFi Router/Hotspot** | 1 | 0 | 0 | Use mobile hotspot |

**TOTAL: ₹3,360 - ₹4,000**

### **Option B: Demo/Simulation Only (₹800 - ₹1,500)**

| Component | Quantity | Unit Price (INR) | Total (INR) | Purpose |
|-----------|----------|------------------|-------------|---------|
| **ESP32 DevKit** | 1 | 350 | 350 | Simulate sensor data |
| **Potentiometers** | 3 | 30 | 90 | Manual input sliders |
| **LEDs (various colors)** | 10 | 5 | 50 | Visual indicators |
| **Resistors** | 10 | 1 | 10 | LED current limiting |
| **Breadboard** | 1 | 50 | 50 | Prototyping |
| **Jumper Wires** | 1 pack | 50 | 50 | Connections |
| **Cardboard Model** | - | 100 | 100 | Campus building mockup |
| **Craft Supplies** | - | 100 | 100 | Decorative materials |

**TOTAL: ₹800 - ₹1,000**

### **Option C: Software-Only (₹0)**
- Use existing simulation code (already in repo)
- Focus on dashboard polish, ML model accuracy
- Create impressive visualizations
- **Cost: ₹0** (no hardware)

**Recommendation:** Choose **Option B** for budget-conscious teams. It provides tangible hardware interaction while keeping costs under ₹1,500.

---

## 🔌 Circuit Diagrams

### **Circuit 1: Solar Panel Monitoring**

```
Solar Panel (5-10W, ~6-12V)
    │
    ├──[+]──> Voltage Divider (10kΩ + 10kΩ) ──> ESP32 GPIO34 (ADC1_CH6)
    │
    ├──[+]──> ACS712 Current Sensor [VCC=5V, OUT] ──> ESP32 GPIO35 (ADC1_CH7)
    │                                   │
    ├──────> [ACS712 IP+]              │
    │                                   │
    └──[−]──> [ACS712 IP−] ──> GND     │
                                        │
                            [OUT] ──────┘

Notes:
- Voltage divider: 10kΩ from V+ to ADC, 10kΩ from ADC to GND (halves voltage)
- ACS712: Vout = 2.5V at 0A, ±0.185V per amp (5A version)
- ESP32 ADC: 0-3.3V range (use voltage divider if solar > 6.6V)
```

### **Circuit 2: Battery State-of-Charge Monitoring**

```
Battery Pack (4× 18650 = 14.8V nominal)
    │
    ├──[+]──> Voltage Divider (22kΩ + 10kΩ) ──> ESP32 GPIO32 (ADC1_CH4)
    │                                               │
    │                                              GND
    │
    ├──[+]──> TP4056 Charging Module [OUT+]
    │             │
    │             [IN+] ←── Solar Panel [+]
    │             [IN−] ←── Solar Panel [−]
    │
    └──[−]──> TP4056 [OUT−] ──> GND

Notes:
- Voltage divider: 22kΩ + 10kΩ = divides by 3.2 (14.8V → 4.6V → use 2.2kΩ+1kΩ for 3.3V max)
- TP4056: Automatic CC/CV charging for Li-Ion batteries
- Add protection circuit if batteries don't have built-in BMS
```

### **Circuit 3: Campus Load Simulation (LEDs)**

```
ESP32 GPIO Pins → LED Arrays (representing buildings)

Building 1 (Academic Block):
GPIO25 ──> [220Ω] ──> LED1 (White) ──> GND
GPIO26 ──> [220Ω] ──> LED2 (White) ──> GND
GPIO27 ──> [220Ω] ──> LED3 (White) ──> GND

Building 2 (Hostel):
GPIO14 ──> [220Ω] ──> LED4 (Yellow) ──> GND
GPIO12 ──> [220Ω] ──> LED5 (Yellow) ──> GND

Grid Import Indicator:
GPIO13 ──> [220Ω] ──> LED6 (Red) ──> GND

Battery Charge Indicator:
GPIO15 ──> [220Ω] ──> LED7 (Green) ──> GND

Notes:
- Use PWM on GPIO pins to vary LED brightness (simulates variable load)
- 220Ω resistor for 3.3V → ~10mA per LED
- Total current: <100mA (safe for ESP32)
```

### **Circuit 4: Environmental Sensors**

```
DHT22 Temperature & Humidity Sensor:
    [VCC] ──> ESP32 3.3V
    [DATA] ──> ESP32 GPIO4 (with 10kΩ pull-up to 3.3V)
    [GND] ──> GND

BH1750 Light Intensity Sensor (I2C):
    [VCC] ──> ESP32 3.3V
    [GND] ──> GND
    [SDA] ──> ESP32 GPIO21 (I2C Data)
    [SCL] ──> ESP32 GPIO22 (I2C Clock)

Notes:
- DHT22: ±0.5°C temperature accuracy
- BH1750: Digital lux meter (0-65535 lux), I2C address 0x23
- Alternative: Use simple LDR + voltage divider (cheaper)
```

### **Circuit 5: Complete System Integration**

```
                    ┌─────────────────────────────────────┐
                    │         SOLAR PANEL (5-10W)         │
                    └────────────┬───────────┬────────────┘
                                 │           │
                            [Voltage]    [Current]
                            Sensor       Sensor
                                 │           │
                    ┌────────────▼───────────▼────────────┐
                    │        TP4056 CHARGER MODULE        │
                    │      [Protection + CC/CV Charge]    │
                    └────────────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────┐
                    │    BATTERY PACK (4× 18650 Cells)    │
                    │         ~14.8V, 2500-3000mAh        │
                    └────────────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────┐
                    │      DC-DC BUCK CONVERTER           │
                    │         (14.8V → 5V)                │
                    └────────────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────┐
                    │          ESP32 DevKit               │
                    │    ┌─────────────────────────┐      │
                    │    │  GPIO34 ← Solar Voltage │      │
                    │    │  GPIO35 ← Solar Current │      │
                    │    │  GPIO32 ← Battery Voltage│      │
                    │    │  GPIO4  ← DHT22 Temp    │      │
                    │    │  GPIO21/22 ← BH1750 Lux │      │
                    │    │  GPIO25-27 → LEDs (Load)│      │
                    │    │  GPIO13-15 → Indicators │      │
                    │    │  WiFi → MQTT/HTTP       │      │
                    │    └─────────────────────────┘      │
                    └─────────────────────────────────────┘
                                 │
                            [WiFi Network]
                                 │
                    ┌────────────▼────────────────────────┐
                    │    LAPTOP (Dashboard Server)        │
                    │  - Streamlit Dashboard              │
                    │  - ML Models (Prediction/Anomaly)   │
                    │  - Data Storage & Visualization     │
                    └─────────────────────────────────────┘
```

---

## 🏗️ Physical Setup Options

### **Option 1: No Physical Model (Software Only)**
- **Pros:** Zero cost, focus on software quality
- **Cons:** Less visually impressive
- **Verdict:** Good for strong software teams with limited budget

### **Option 2: Cardboard Campus Mockup (Recommended)**
- **Materials:** Cardboard boxes, paper, markers, glue
- **Design:**
  - 3-4 cardboard "buildings" (academic block, hostel, library)
  - Mini solar panel on "rooftop"
  - LEDs inside buildings (visible through windows)
  - Battery pack mounted on side panel
  - ESP32 in "control room" box
- **Cost:** ₹200-300
- **Verdict:** ⭐ Best balance of cost and visual impact

### **Option 3: Acrylic/3D-Printed Model**
- **Pros:** Professional appearance
- **Cons:** Expensive (₹2,000-5,000), time-consuming
- **Verdict:** Only if you have pre-made components

### **Do You Need a Mini Town?**
**Answer: Not necessary, but recommended for visual impact.**

A simple 2D or 3D cardboard model showing:
- 3-4 buildings with LEDs (representing energy consumption)
- Solar panel on top
- Battery pack labeled clearly
- ESP32 + sensors mounted visibly

This helps judges **see** the digital twin concept physically. Spend max 2-3 hours on this.

---

## 📊 Training Data & Model Development

### **What Data to Use?**

Your repo already has a **synthetic data generator** (`src/data/iot_simulator.py`). This generates:
- 90 days of 15-minute interval data
- Solar generation (based on hour, cloud cover)
- Campus demand (weekday/weekend patterns)
- Battery state-of-charge
- Temperature, irradiance
- Anomalies (~1% of samples)

**For the hackathon, you have 3 data sources:**

#### **1. Synthetic Data (Already Implemented) ⭐ BEST OPTION**
- **Pros:**
  - Already works perfectly
  - Realistic patterns (weekday/weekend, day/night)
  - Configurable parameters
  - No external dependencies
- **Cons:** Not "real" data
- **How to use:** Already integrated in dashboard, just run it!

```python
from src.data.iot_simulator import generate_iot_data

# Generate 90 days of data
df = generate_iot_data(days=90, solar_capacity_kw=300, battery_capacity_kwh=500)
```

#### **2. Live Hardware Data (If you build Option A/B)**
- **Pros:**
  - Real sensor readings
  - Impressive to judges
- **Cons:**
  - Only 2 days of data (not enough for training)
  - Need hardware working perfectly
- **How to use:**
  - Use synthetic data for **training models**
  - Use live hardware for **real-time dashboard demo**

#### **3. Public Energy Datasets (Optional)**
- **Sources:**
  - NREL Solar Radiation Database: https://nsrdb.nrel.gov/
  - OpenEI: https://openei.org/datasets
  - Kaggle Energy Datasets
- **Pros:** Real-world data
- **Cons:** Time-consuming to clean and adapt
- **Verdict:** Skip this for 2-day hackathon

### **Training the Models: Step-by-Step**

The models are **already trained automatically** when you run the dashboard. But here's the manual process if needed:

#### **Step 1: Generate Training Data**
```python
from src.data.iot_simulator import generate_iot_data

# Generate 90 days of historical data
df = generate_iot_data(
    start_date="2024-01-01",
    days=90,
    interval_minutes=15,
    solar_capacity_kw=300,
    battery_capacity_kwh=500
)

# Save for later use
df.to_csv("training_data.csv", index=False)
```

#### **Step 2: Train Energy Prediction Models**
```python
from src.models.energy_predictor import EnergyPredictor

# Initialize and train
predictor = EnergyPredictor(n_estimators=100, random_state=42)
predictor.fit(df, test_size=0.2)

# Check performance
print(f"Demand MAE: {predictor.metrics['demand_mae']:.2f} kW")
print(f"Demand R²: {predictor.metrics['demand_r2']:.3f}")
print(f"Solar MAE: {predictor.metrics['solar_mae']:.2f} kW")
print(f"Solar R²: {predictor.metrics['solar_r2']:.3f}")

# Save model for deployment
predictor.save("models/trained_predictor/")
```

#### **Step 3: Train Anomaly Detection Model**
```python
from src.models.anomaly_detector import AnomalyDetector

# Initialize and train
detector = AnomalyDetector(contamination=0.05, random_state=42)
detector.fit(df)

# Test on same data
result_df = detector.predict(df)
anomalies = result_df[result_df["is_anomaly_any"] == 1]
print(f"Detected {len(anomalies)} anomalies out of {len(df)} samples")

# Save model
detector.save("models/trained_detector/")
```

#### **Step 4: Test Predictions**
```python
# Load models
predictor = EnergyPredictor.load("models/trained_predictor/")

# Get latest reading
latest = df.iloc[-1]

# Predict next 4 hours (16 steps × 15 min)
forecast = predictor.predict_horizon(latest, horizon_steps=16)
print(forecast)
```

### **Model Hyperparameter Tuning (Optional)**

If you have time on Day 2 and want better accuracy:

```python
# Try different Random Forest parameters
predictor = EnergyPredictor(n_estimators=200, random_state=42)  # More trees
predictor.fit(df, test_size=0.2)

# Or tune anomaly detector sensitivity
detector = AnomalyDetector(contamination=0.03, random_state=42)  # Less sensitive
detector.fit(df)
```

**Recommendation:** Don't spend time on this during hackathon. Current models already achieve R² > 0.70, which is good enough.

---

## 🔬 FPGA Integration (Optional Advanced Feature)

### **Should You Use FPGA?**

**Pros:**
- Impressive for judges (hardware acceleration)
- Real-time processing at high speed
- Unique differentiator from other teams

**Cons:**
- Complex to implement in 2 days
- Risk of wasting time on debugging
- Not essential for digital twin functionality

### **Verdict: Only if you have prior FPGA experience**

### **Where FPGA Fits In:**

```
Sensor Data → ESP32 → FPGA → Laptop
                         │
                         ├─> Fast anomaly detection (hardware accelerated)
                         ├─> Real-time power flow calculations
                         └─> Edge processing (reduce latency)
```

### **Implementation Options:**

#### **Option 1: Use FPGA for Real-Time Anomaly Detection**

**Hardware:** Xilinx Artix-7, Intel MAX10, or Lattice iCE40

**Approach:**
- Implement a simple threshold-based anomaly detector in Verilog/VHDL
- FPGA receives sensor data via UART from ESP32
- Computes rolling statistics (mean, std dev) in hardware
- Flags anomalies if value > mean + 2×std
- Sends flag to laptop via USB/UART

**Estimated Time:** 6-8 hours (experienced FPGA developer)

#### **Option 2: Use FPGA for Power Flow Calculations**

```verilog
module power_optimizer (
    input clk,
    input [15:0] solar_gen_kw,
    input [15:0] demand_kw,
    input [15:0] battery_soc_pct,
    output reg [15:0] grid_import_kw,
    output reg [15:0] battery_action
);

always @(posedge clk) begin
    if (solar_gen_kw > demand_kw) begin
        grid_import_kw <= 0;
        battery_action <= 1; // charge
    end else begin
        grid_import_kw <= demand_kw - solar_gen_kw;
        battery_action <= 2; // discharge
    end
end

endmodule
```

**Verdict:** Skip FPGA unless you already have working code. It's not required to win.

---

## ✅ Testing Checklist

### **Hardware Tests (Day 1 Evening)**

- [ ] Solar panel outputs correct voltage (6-12V in sunlight/lamp)
- [ ] Current sensor reads correct values (test with known load)
- [ ] Battery voltage reading is accurate (compare with multimeter)
- [ ] Temperature sensor returns values in range (15-40°C)
- [ ] Light sensor responds to brightness changes
- [ ] LEDs light up when GPIO pins are HIGH
- [ ] ESP32 connects to WiFi successfully
- [ ] ESP32 sends data to laptop (MQTT/HTTP)

### **Software Tests (Day 2 Morning)**

- [ ] Dashboard loads without errors (`streamlit run src/dashboard/app.py`)
- [ ] All 4 tabs display correctly (Energy, AI, Optimizer, Anomaly)
- [ ] Live data from ESP32 appears in dashboard
- [ ] Prediction model generates forecasts
- [ ] Anomaly detector flags abnormal readings
- [ ] Optimizer recommendations make sense
- [ ] Auto-refresh works (10-second updates)
- [ ] Can adjust sliders (solar capacity, battery size)

### **Integration Tests (Day 2 Afternoon)**

- [ ] Cover solar panel → dashboard shows reduced generation
- [ ] Turn on LEDs → dashboard shows increased demand
- [ ] Disconnect battery → dashboard flags anomaly
- [ ] Change time of day → predictions update
- [ ] Works on presentation laptop (not just dev machine)
- [ ] Demo runs for 5+ minutes without crash
- [ ] Backup video demo recorded (in case live demo fails)

### **Unit Tests (Already Implemented)**

Run the existing test suite:
```bash
python -m pytest tests/ -v
```

All tests should pass:
- `test_iot_simulator.py` - 18 tests
- `test_energy_predictor.py` - 13 tests
- `test_anomaly_detector.py` - 13 tests
- `test_optimizer.py` - 31 tests

---

## 🎤 Presentation Strategy (How to Win)

### **Presentation Structure (8-10 minutes)**

#### **1. Hook (30 seconds)**
> "Imagine if your campus could predict energy demand 4 hours in advance, automatically optimize battery usage, and detect equipment failures before they happen. That's what our digital twin does."

#### **2. Problem Statement (1 minute)**
- Campus energy bills are rising (peak demand charges)
- Solar energy is wasted during low-demand periods
- Battery systems aren't optimized
- Equipment failures cause disruptions

#### **3. Solution Overview (1.5 minutes)**
Show architecture diagram:
```
IoT Sensors → ESP32 → WiFi → Digital Twin Dashboard
                              ↓
                    [ML Models] [Optimizer] [Anomaly Detector]
                              ↓
                      Real-time Recommendations
```

Highlight 4 key features:
1. **Real-time monitoring** (live sensor data)
2. **AI prediction** (4-24 hours ahead)
3. **Optimization** (reduces grid import by 30-40%)
4. **Fault detection** (prevents equipment failures)

#### **4. Live Demo (3-4 minutes)**

**Sequence:**
1. Show live dashboard with real sensor data
2. Navigate through 4 tabs:
   - Energy Overview (power flow chart)
   - AI Predictions (forecast chart)
   - Optimizer (battery actions)
   - Anomaly Detection (fault flags)
3. **Interactive moment:**
   - Cover solar panel with hand → watch dashboard react
   - Turn on LEDs → show demand spike + optimizer response
4. Show cost savings KPI (₹X saved in 90 days)

#### **5. Technical Deep Dive (1.5 minutes)**
- ML models: Random Forest (100 trees) with R² > 0.70
- Anomaly detection: Hybrid ML (Isolation Forest) + rule-based
- Optimizer: Greedy dispatch with peak/off-peak tariffs
- Hardware: ESP32 + 6 sensors + solar panel + battery

#### **6. Impact & Scalability (1 minute)**
- Reduces campus energy costs by 25-35%
- Enables proactive maintenance (prevents failures)
- Scalable to entire university campus
- Can integrate with existing BMS (Building Management Systems)

#### **7. Closing (30 seconds)**
> "Our digital twin doesn't just monitor energy—it predicts, optimizes, and protects. This is the future of smart campuses."

### **Demo Best Practices**

✅ **DO:**
- Test demo 3+ times before presentation
- Have backup video recording
- Use large fonts (18pt minimum)
- Show live hardware interaction
- Mention technologies (Python, ML, IoT, ESP32)
- Emphasize cost savings and ROI

❌ **DON'T:**
- Spend too much time on code
- Read from slides
- Ignore hardware in demo
- Go over time limit
- Forget to show KPIs (judges love numbers)

### **Slide Deck Outline (10-12 slides)**

1. Title slide (team name, project name)
2. Problem statement (with statistics)
3. Solution overview (architecture diagram)
4. Feature 1: Real-time monitoring
5. Feature 2: AI predictions
6. Feature 3: Optimization
7. Feature 4: Anomaly detection
8. Hardware setup (photo of physical prototype)
9. Technical stack (logos: Python, TensorFlow, ESP32, etc.)
10. Results & impact (cost savings, efficiency gains)
11. Future work & scalability
12. Thank you + Q&A

---

## 🚨 Emergency Backup Plan

### **If Hardware Fails:**
- Switch to simulation mode (already in repo)
- Show synthetic data dashboard
- Explain: "Hardware prototype for demo, but software works with any sensors"

### **If WiFi Fails:**
- Use mobile hotspot
- Or pre-record demo video and play it

### **If Dashboard Crashes:**
- Have backup video recording
- Or show screenshots of each tab

### **If Model Training Fails:**
- Use pre-trained models (run training on Day 1 and save)
- Load saved models: `predictor.load("models/")`

### **If You Run Out of Time:**
- Prioritize software polish over hardware
- A working dashboard with synthetic data > broken hardware prototype

---

## 📦 Deliverables Checklist

### **Code Repository**
- [ ] All code pushed to GitHub
- [ ] README.md updated with setup instructions
- [ ] Requirements.txt with all dependencies
- [ ] HACKATHON_GUIDE.md (this document)

### **Physical Prototype**
- [ ] Working hardware (or cardboard model)
- [ ] All components labeled clearly
- [ ] Portable (fits in backpack/box)

### **Presentation Materials**
- [ ] Slide deck (PDF + PPT)
- [ ] Demo video (3-5 minutes)
- [ ] Architecture diagram
- [ ] Circuit diagrams

### **Documentation**
- [ ] System architecture diagram
- [ ] API documentation (if applicable)
- [ ] User guide for dashboard

---

## 🎯 Success Metrics (What Judges Look For)

1. **Innovation:** Combining IoT + ML + optimization (✅ you have this)
2. **Completeness:** Full end-to-end system (hardware → software → dashboard)
3. **Impact:** Clear cost savings and efficiency gains
4. **Technical Depth:** ML models, optimization algorithms, real-time processing
5. **Presentation:** Clear demo, confident delivery, good storytelling
6. **Scalability:** Can this work for entire campus? Other universities?

---

## 💡 Pro Tips for Winning

1. **Focus on polish, not features:** A working demo with 3 features beats a buggy demo with 10
2. **Show, don't tell:** Live hardware interaction is more impressive than slides
3. **Emphasize cost savings:** Judges love ROI (₹X saved per year)
4. **Practice presentation 3+ times:** Smooth delivery > technical perfection
5. **Have a backup plan:** Video demo if live demo fails
6. **Use the existing code:** Your repo already has 90% of what you need
7. **Dress professionally:** First impressions matter
8. **Arrive early:** Test setup in presentation room
9. **Handle Q&A confidently:** If you don't know, say "Great question, we'd explore that in future work"
10. **Smile and enjoy:** Confidence and enthusiasm are contagious

---

## 📞 Day-Of-Hackathon Quick Reference

### **ESP32 Firmware Template (Arduino)**

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// WiFi credentials
const char* ssid = "YourNetworkName";
const char* password = "YourPassword";

// Server endpoint
const char* serverURL = "http://192.168.1.100:5000/api/sensor-data";

// Pin definitions
#define SOLAR_VOLTAGE_PIN 34
#define SOLAR_CURRENT_PIN 35
#define BATTERY_VOLTAGE_PIN 32
#define DHT_PIN 4
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // Initialize sensors
  dht.begin();
}

void loop() {
  // Read sensors
  int solarVoltageRaw = analogRead(SOLAR_VOLTAGE_PIN);
  int solarCurrentRaw = analogRead(SOLAR_CURRENT_PIN);
  int batteryVoltageRaw = analogRead(BATTERY_VOLTAGE_PIN);

  // Convert ADC values to real units
  float solarVoltage = (solarVoltageRaw / 4095.0) * 3.3 * 2.0; // voltage divider factor
  float solarCurrent = ((solarCurrentRaw / 4095.0) * 3.3 - 2.5) / 0.185; // ACS712
  float batteryVoltage = (batteryVoltageRaw / 4095.0) * 3.3 * 3.2; // voltage divider
  float solarPower = solarVoltage * solarCurrent;

  // Read temperature
  float temperature = dht.readTemperature();

  // Create JSON payload
  String jsonData = "{";
  jsonData += "\"solar_gen_kw\":" + String(solarPower / 1000.0, 2) + ",";
  jsonData += "\"battery_voltage\":" + String(batteryVoltage, 2) + ",";
  jsonData += "\"temperature_c\":" + String(temperature, 2);
  jsonData += "}";

  // Send HTTP POST
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonData);

    Serial.print("HTTP Response: ");
    Serial.println(httpResponseCode);

    http.end();
  }

  delay(15000); // Send data every 15 seconds
}
```

### **Quick Commands**

```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run src/dashboard/app.py

# Run tests
python -m pytest tests/ -v

# Generate training data manually
python -c "from src.data.iot_simulator import generate_iot_data; df = generate_iot_data(days=90); df.to_csv('data.csv')"

# Train models manually
python -c "from src.data.iot_simulator import generate_iot_data; from src.models.energy_predictor import EnergyPredictor; df = generate_iot_data(days=90); p = EnergyPredictor(); p.fit(df); p.save('models/')"
```

---

## ✨ Final Checklist

**Friday Night (Preparation):**
- [ ] Clone repo and test dashboard locally
- [ ] Buy hardware components (if doing Option A/B)
- [ ] Assign team roles
- [ ] Read this guide fully

**Saturday Morning:**
- [ ] Arrive with all team members + hardware
- [ ] Set up workspace (table, power, WiFi)
- [ ] Run existing code to verify it works

**Saturday Afternoon:**
- [ ] Assemble hardware circuits
- [ ] Test sensor readings with multimeter
- [ ] Write ESP32 firmware

**Saturday Evening:**
- [ ] Connect ESP32 to dashboard
- [ ] Build physical prototype model
- [ ] Test end-to-end system

**Sunday Morning:**
- [ ] Fix any bugs from Day 1
- [ ] Add polish features (animations, better UI)
- [ ] Finalize physical prototype

**Sunday Afternoon:**
- [ ] Create presentation slides
- [ ] Record backup demo video
- [ ] Practice presentation 3 times
- [ ] Prepare for Q&A

**Presentation Time:**
- [ ] Arrive 30 min early
- [ ] Test setup in presentation room
- [ ] Deliver confidently
- [ ] WIN! 🏆

---

## 🙏 Good Luck!

You have a **solid codebase** with working ML models, optimization, and dashboard. Your main tasks are:

1. Add simple hardware integration (ESP32 + sensors)
2. Build a visual prototype (cardboard model)
3. Polish the presentation
4. Practice the demo

**You've got this!** 💪

---

**Questions? Check these resources:**
- ESP32 Arduino Core: https://github.com/espressif/arduino-esp32
- Streamlit Docs: https://docs.streamlit.io
- scikit-learn: https://scikit-learn.org

**Team Contact:** [Add your email/phone here]
