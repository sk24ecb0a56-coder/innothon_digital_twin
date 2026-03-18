# Hardware Integration Guide

This directory contains all hardware-related code and documentation for the Campus Energy Digital Twin project.

---

## 📁 Contents

```
hardware/
├── README.md                      (this file)
├── CIRCUIT_DIAGRAMS.md            (detailed wiring diagrams)
├── esp32_firmware/
│   └── campus_energy_sensor.ino   (ESP32 Arduino firmware)
└── esp32_data_receiver.py         (Python HTTP server for live data)
```

---

## 🚀 Quick Start

### Step 1: Hardware Assembly

1. Follow the circuit diagrams in `CIRCUIT_DIAGRAMS.md`
2. Wire the ESP32 to sensors according to pin assignments
3. Test each sensor individually before full integration

### Step 2: Upload ESP32 Firmware

1. Install Arduino IDE: https://www.arduino.cc/en/software
2. Install ESP32 board support:
   - File → Preferences
   - Add to "Additional Boards Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install
3. Install required libraries:
   - Sketch → Include Library → Manage Libraries
   - Search and install:
     - `DHT sensor library` by Adafruit
     - `Adafruit Unified Sensor`
     - `BH1750` by Christopher Laws
     - `ArduinoJson` by Benoit Blanchon
4. Open `esp32_firmware/campus_energy_sensor.ino`
5. Configure WiFi credentials and server URL (lines 23-27)
6. Select board: Tools → Board → ESP32 Dev Module
7. Select port: Tools → Port → (your ESP32 port)
8. Upload: Sketch → Upload (or Ctrl+U)
9. Open Serial Monitor (115200 baud) to verify operation

### Step 3: Start Data Receiver Server

On your laptop (same WiFi network as ESP32):

```bash
# Install Flask if not already installed
pip install flask

# Find your laptop IP address
# Linux/Mac:
ifconfig | grep "inet "
# Windows:
ipconfig

# Update ESP32 firmware with your laptop IP (line 27)
# Then run the server:
python hardware/esp32_data_receiver.py
```

The server will start on `http://0.0.0.0:5000` and wait for ESP32 connections.

### Step 4: Verify Data Flow

1. Power on ESP32 (via USB or battery)
2. Check Serial Monitor - should see "WiFi connected" and "Data sent"
3. Check server terminal - should see "Received data" messages
4. Verify file created: `live_sensor_data.json`

---

## 🔌 Pin Assignments (ESP32)

| GPIO | Function | Connected To |
|------|----------|--------------|
| GPIO34 (ADC1_CH6) | Analog Input | Solar voltage divider |
| GPIO35 (ADC1_CH7) | Analog Input | Solar current sensor (ACS712) |
| GPIO32 (ADC1_CH4) | Analog Input | Battery voltage divider |
| GPIO4 | Digital I/O | DHT22 temperature sensor (DATA) |
| GPIO21 | I2C SDA | BH1750 light sensor |
| GPIO22 | I2C SCL | BH1750 light sensor |
| GPIO25 | PWM Output | Building 1 LED |
| GPIO26 | PWM Output | Building 2 LED |
| GPIO27 | PWM Output | Building 3 LED |
| GPIO13 | PWM Output | Grid import LED (Red) |
| GPIO15 | PWM Output | Battery LED (Green) |
| GPIO2 | Digital Output | Status LED (built-in) |

---

## 📊 Data Format

The ESP32 sends JSON data to the server every 15 seconds:

```json
{
  "timestamp": 12345678,
  "solar_gen_kw": 0.245,
  "solar_voltage": 8.3,
  "solar_current": 0.03,
  "battery_voltage": 14.2,
  "battery_soc_pct": 65.5,
  "temperature_c": 27.3,
  "irradiance_lux": 45230,
  "irradiance_norm": 0.452,
  "demand_kw": 0.387,
  "grid_import_kw": 0.142
}
```

---

## 🔧 Configuration

### WiFi Settings

Edit `esp32_firmware/campus_energy_sensor.ino` lines 23-24:

```cpp
const char* WIFI_SSID = "YourWiFiName";
const char* WIFI_PASSWORD = "YourWiFiPassword";
```

### Server Endpoint

Update line 27 with your laptop's IP address:

```cpp
const char* SERVER_URL = "http://192.168.1.100:5000/api/sensor-data";
```

To find your laptop IP:
- **Windows:** `ipconfig` → look for "IPv4 Address"
- **Mac/Linux:** `ifconfig` → look for "inet" under active network interface
- Must be on same WiFi network as ESP32

### System Parameters

Adjust solar/battery capacity in `esp32_firmware/campus_energy_sensor.ino` lines 30-31:

```cpp
const float SOLAR_CAPACITY_KW = 0.300;  // 300W = 0.3 kW
const float BATTERY_CAPACITY_KWH = 0.5; // 500Wh = 0.5 kWh
```

### Sampling Interval

Change data collection frequency (line 50):

```cpp
const unsigned long SAMPLE_INTERVAL_MS = 15000; // 15 seconds
```

---

## 🧪 Testing Individual Components

### Test 1: ESP32 WiFi Connection

Upload and run this minimal test:

```cpp
#include <WiFi.h>

const char* ssid = "YourWiFiName";
const char* password = "YourPassword";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
}

void loop() {}
```

### Test 2: Solar Voltage Measurement

```cpp
void setup() {
  Serial.begin(115200);
}

void loop() {
  int raw = analogRead(34);
  float voltage = (raw / 4095.0) * 3.3 * 2.0; // voltage divider factor
  Serial.printf("Raw: %d, Voltage: %.2f V\n", raw, voltage);
  delay(1000);
}
```

### Test 3: DHT22 Temperature

```cpp
#include <DHT.h>

DHT dht(4, DHT22);

void setup() {
  Serial.begin(115200);
  dht.begin();
}

void loop() {
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  Serial.printf("Temp: %.1f°C, Humidity: %.1f%%\n", temp, humidity);
  delay(2000);
}
```

### Test 4: BH1750 Light Sensor

```cpp
#include <Wire.h>
#include <BH1750.h>

BH1750 lightMeter;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  lightMeter.begin();
}

void loop() {
  float lux = lightMeter.readLightLevel();
  Serial.printf("Light: %.0f lux\n", lux);
  delay(1000);
}
```

---

## 🐛 Troubleshooting

### ESP32 Not Connecting to WiFi

1. Verify SSID and password are correct
2. Check if router is 2.4GHz (ESP32 doesn't support 5GHz)
3. Move ESP32 closer to router
4. Check Serial Monitor for error messages

### Server Not Receiving Data

1. Verify laptop and ESP32 are on same WiFi network
2. Check laptop firewall isn't blocking port 5000
3. Verify server URL in ESP32 code matches laptop IP
4. Check server terminal for error messages
5. Test endpoint manually: `curl http://localhost:5000/health`

### Sensor Reading Errors

1. **DHT22 returns NaN:**
   - Check 10kΩ pull-up resistor on DATA line
   - Wait 2+ seconds between readings
   - Verify VCC is 3.3V

2. **BH1750 not detected:**
   - Verify I2C wiring (SDA ↔ GPIO21, SCL ↔ GPIO22)
   - Check I2C address (usually 0x23)
   - Test with I2C scanner code

3. **ADC always reads 0 or 4095:**
   - Check voltage divider resistor values
   - Measure voltage at ADC pin with multimeter
   - Ensure voltage is < 3.3V (ESP32 ADC limit)

### Battery Issues

1. **Battery drains quickly:**
   - Reduce LED brightness
   - Increase sampling interval (15s → 60s)
   - Use ESP32 deep sleep mode
   - Check for short circuits

2. **Battery not charging:**
   - Verify solar panel produces voltage in sunlight
   - Check charger LED indicators
   - Measure battery voltage with multimeter
   - Ensure battery isn't over-discharged (<3.0V per cell)

---

## 🔋 Power Management

### Normal Operation
- Current draw: ~230mA
- Battery life: ~47 hours (2500mAh battery)
- Self-sufficient with 3+ hours of sunlight per day

### Deep Sleep Mode (Optional)

Add to end of `loop()` function:

```cpp
// Send data, then sleep for 60 seconds
Serial.println("Going to deep sleep...");
esp_sleep_enable_timer_wakeup(60 * 1000000); // 60 seconds
esp_deep_sleep_start();
// ESP32 will restart after 60 seconds
// Current draw: ~10µA (vs 160mA active)
```

**Note:** In deep sleep, WiFi disconnects and ESP32 reboots on wake.

---

## 📡 API Endpoints

### POST /api/sensor-data
Receive sensor data from ESP32.

**Request:**
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"solar_gen_kw": 0.25, "demand_kw": 0.38, "battery_soc_pct": 65.0}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Data received"
}
```

### GET /api/sensor-data
Retrieve latest sensor reading.

**Request:**
```bash
curl http://localhost:5000/api/sensor-data
```

**Response:** (same as POST data, plus server_timestamp)

### GET /health
Health check endpoint.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-18T12:34:56",
  "data_available": true
}
```

---

## 🔗 Integrating with Dashboard

To display live hardware data in the Streamlit dashboard:

1. Modify `src/dashboard/app.py` to read from `live_sensor_data.json`
2. Add fallback to simulated data if file doesn't exist
3. Update every 10-15 seconds

Example code:

```python
import json
import os

def get_live_or_simulated_data(solar_capacity_kw=300):
    """Try to read live data, fallback to simulation."""
    if os.path.exists("live_sensor_data.json"):
        with open("live_sensor_data.json", "r") as f:
            data = json.load(f)
        # Check if data is recent (< 60 seconds old)
        from datetime import datetime
        server_time = datetime.fromisoformat(data.get("server_timestamp", "2000-01-01"))
        age_seconds = (datetime.now() - server_time).total_seconds()
        if age_seconds < 60:
            return data, "live"

    # Fallback to simulation
    from src.data.iot_simulator import get_live_reading
    return get_live_reading(solar_capacity_kw=solar_capacity_kw), "simulated"
```

---

## 📦 Required Libraries

**Arduino Libraries** (install via Library Manager):
- DHT sensor library (Adafruit)
- Adafruit Unified Sensor
- BH1750 (Christopher Laws)
- ArduinoJson (Benoit Blanchon)

**Python Libraries** (install via pip):
```bash
pip install flask
```

---

## 🎓 Learning Resources

**ESP32:**
- Official documentation: https://docs.espressif.com/projects/esp-idf/
- Arduino core: https://github.com/espressif/arduino-esp32

**Sensors:**
- DHT22 datasheet: https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf
- BH1750 datasheet: https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf
- ACS712 datasheet: https://www.allegromicro.com/en/products/sense/current-sensor-ics/zero-to-fifty-amp-integrated-conductor-sensor-ics/acs712

**Circuit Design:**
- Voltage dividers: https://www.electronics-tutorials.ws/resistor/res_2.html
- Li-Ion safety: https://batteryuniversity.com/article/bu-410-charging-at-high-and-low-temperatures

---

## 🆘 Support

If you encounter issues during the hackathon:

1. Check the troubleshooting section above
2. Review `CIRCUIT_DIAGRAMS.md` for wiring verification
3. Test each component individually
4. Use Serial Monitor to debug ESP32 (115200 baud)
5. Check server logs for HTTP errors

**Remember:** It's okay to switch to simulated data if hardware isn't working perfectly. The judges will appreciate a working demo more than perfect hardware.

---

## ✅ Pre-Hackathon Checklist

- [ ] All components purchased and received
- [ ] Arduino IDE installed with ESP32 support
- [ ] Required libraries installed
- [ ] ESP32 firmware uploaded successfully
- [ ] Each sensor tested individually
- [ ] Full circuit assembled on breadboard
- [ ] WiFi connection verified
- [ ] Data receiver server running
- [ ] Live data appearing in `live_sensor_data.json`
- [ ] Physical prototype (cardboard model) built
- [ ] LEDs working and visible
- [ ] System can run for 30+ minutes without crashes
- [ ] Backup plan ready (simulation mode)

---

## 🚀 Hackathon Day Strategy

**Saturday Morning:**
- Assemble hardware and test basic functionality
- Upload firmware and verify WiFi connection

**Saturday Afternoon:**
- Integrate with dashboard
- Build physical model

**Saturday Evening:**
- End-to-end testing
- Fix any critical bugs

**Sunday:**
- Polish presentation
- Record backup demo video
- Practice live demo

---

Good luck! 🎉
