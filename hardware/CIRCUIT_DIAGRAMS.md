# Circuit Diagrams for Campus Energy Digital Twin

Complete wiring diagrams for the hardware prototype.

---

## Component Reference Table

| Symbol | Component | Pins/Terminals |
|--------|-----------|----------------|
| ESP32 | ESP32 DevKit v1 | 38 pins total |
| DHT22 | Temperature/Humidity Sensor | VCC, GND, DATA |
| BH1750 | Digital Light Sensor | VCC, GND, SDA, SCL |
| ACS712 | Current Sensor (5A) | VCC, GND, OUT, IP+, IP- |
| TP4056 | Li-Ion Charging Module | IN+, IN-, OUT+, OUT-, B+, B- |
| LM2596 | Buck Converter (adjustable) | IN+, IN-, OUT+, OUT- |
| 18650 | Lithium-Ion Battery | + terminal, - terminal |

---

## Full System Wiring Diagram

```
                    SOLAR PANEL (5-10W, 6-12V)
                            │
                            ├──────────┐
                            │          │
                    [Solar Voltage]  [Solar Current]
                      Divider         ACS712
                            │             │
                ┌───────────┴─────────────┴──────────┐
                │                                    │
                │         TP4056 CHARGER             │
                │    [IN+]──Solar[+]                 │
                │    [IN-]──Solar[-]                 │
                │    [OUT+]──Battery[+]              │
                │    [OUT-]──Battery[-]              │
                │    [B+]──Battery[+] (direct)       │
                │    [B-]──Battery[-] (direct)       │
                └───────────┬────────────────────────┘
                            │
                    BATTERY PACK (4× 18650)
                    Nominal: 14.8V (3.7V × 4)
                    Capacity: 2500-3000mAh
                            │
                ┌───────────┴────────────┐
                │                        │
          [Battery Voltage]      LM2596 Buck Converter
            Divider                14.8V → 5V
                │                        │
                │         ┌──────────────┴─────────────┐
                │         │       ESP32 DevKit         │
                │         │    ┌────────────────────┐  │
                │         │    │ USB/VIN ← 5V       │  │
                │         │    │ GND ← GND          │  │
                │         │    │                    │  │
                ├─────────┼────│ GPIO34 ← Solar V   │  │
                │         │    │ GPIO35 ← Solar I   │  │
                └─────────┼────│ GPIO32 ← Battery V │  │
                          │    │                    │  │
                          │    │ GPIO4  → DHT22     │  │
                          │    │ GPIO21 ↔ I2C SDA   │  │
                          │    │ GPIO22 ↔ I2C SCL   │  │
                          │    │                    │  │
                          │    │ GPIO25 → LED1      │  │
                          │    │ GPIO26 → LED2      │  │
                          │    │ GPIO27 → LED3      │  │
                          │    │ GPIO13 → LED_Grid  │  │
                          │    │ GPIO15 → LED_Batt  │  │
                          │    │ GPIO2  → LED_Stat  │  │
                          │    └────────────────────┘  │
                          └────────────────────────────┘
```

---

## Circuit 1: Solar Panel Voltage Measurement

**Purpose:** Measure solar panel voltage (0-12V) with ESP32 ADC (0-3.3V)

```
Solar Panel [+] (6-12V)
    │
    ├──[10kΩ]──┬──> ESP32 GPIO34 (ADC1_CH6)
    │          │
    │      [10kΩ]
    │          │
    └──────────┴──> GND

Formula: V_solar = V_adc × 2.0
Example: If ADC reads 1.5V → Solar panel = 3.0V
```

**Component List:**
- 2× 10kΩ resistors (¼W)
- Breadboard jumper wires

**Notes:**
- This divides voltage by 2 (safe for ESP32)
- For higher voltage (>6.6V), use 22kΩ + 10kΩ (divides by 3.2)
- ADC resolution: 12-bit (0-4095)

---

## Circuit 2: Solar Panel Current Measurement

**Purpose:** Measure current flowing from solar panel (0-5A)

```
Solar Panel [+] ───> [ACS712 IP+]
                          │
Solar Panel [-] ◄─── [ACS712 IP-]

[ACS712 Pinout]
VCC (5V) ──> ESP32 5V (from Buck converter)
GND ──> ESP32 GND
OUT ──> ESP32 GPIO35 (ADC1_CH7)

Output voltage formula:
V_out = 2.5V + (I × 0.185V/A)

Examples:
- 0A   → 2.5V
- 1A   → 2.685V
- 5A   → 3.425V
- -1A  → 2.315V (reverse current)
```

**Component List:**
- 1× ACS712-5A current sensor module
- 3× jumper wires

**Code to calculate current:**
```cpp
float V_out = (analogRead(35) / 4095.0) * 3.3;
float current = (V_out - 2.5) / 0.185;
```

---

## Circuit 3: Battery Voltage Measurement

**Purpose:** Measure 4S Li-Ion battery pack voltage (12-16.8V)

```
Battery [+] (12-16.8V)
    │
    ├──[22kΩ]──┬──> ESP32 GPIO32 (ADC1_CH4)
    │          │
    │      [10kΩ]
    │          │
    └──────────┴──> GND

Formula: V_battery = V_adc × 3.2
Example: If ADC reads 4.0V → Battery = 12.8V

Battery state estimation:
- 16.8V = 100% (fully charged)
- 14.8V = 50% (nominal)
- 12.0V = 0% (empty, do not discharge below this)
```

**Component List:**
- 1× 22kΩ resistor (¼W)
- 1× 10kΩ resistor (¼W)
- Breadboard jumper wires

**Safety Note:**
- Never short battery terminals
- Use batteries with built-in protection circuit (BMS)
- Do not over-discharge below 3.0V per cell (12V total)

---

## Circuit 4: Battery Charging Circuit

**Purpose:** Safely charge 4S Li-Ion battery from solar panel

```
Solar Panel (6-12V)
    │
    ├───[IN+]──┐
    │          │
    └───[IN-]──┤  TP4056 Charging Module
               │  (CC/CV mode, 1A max)
    ┌───[B+]───┤
    │          │
    └───[B-]───┘
    │
    │   4S Battery Pack (4× 18650 in series)
    │   Cell 1 [+]───┬
    │   Cell 2       ├── [+] Terminal (14.8V nominal)
    │   Cell 3       │
    │   Cell 4 [-]───┴── [-] Terminal

LED Indicators on TP4056:
- Red LED: Charging in progress
- Blue LED: Charging complete
```

**Component List:**
- 1× TP4056 charging module
- 4× 18650 Li-Ion cells (3.7V, 2500mAh each)
- 1× 4-cell battery holder

**Important Notes:**
- TP4056 is for **1S** (single cell) Li-Ion charging
- For 4S (4 cells in series), use a **4S BMS board** instead
- Or use 4× separate TP4056 modules (one per cell) - NOT RECOMMENDED
- **Better solution:** Use a dedicated 4S Li-Ion charger module

**Alternative (Recommended for 4S):**
```
Solar Panel → 4S BMS Charger Board → 4S Battery Pack → System
                   ↓
              Protection Features:
              - Overcharge protection (>16.8V)
              - Over-discharge protection (<12V)
              - Short circuit protection
              - Cell balancing
```

---

## Circuit 5: Power Supply (Buck Converter)

**Purpose:** Convert 14.8V battery to 5V for ESP32 and sensors

```
Battery Pack [+] (14.8V)
    │
    ├───[IN+]──┐
    │          │  LM2596 Buck Converter
    └───[IN-]──┤  (Adjustable output)
               │
    ┌───[OUT+]─┤─── 5V → ESP32 VIN
    │          │
    └───[OUT-]─┴─── GND → ESP32 GND

Adjustment:
1. Connect input (14.8V)
2. Turn potentiometer while measuring output
3. Set output to exactly 5.0V
4. Lock potentiometer with glue
```

**Component List:**
- 1× LM2596 buck converter module
- Multimeter (for voltage adjustment)
- Jumper wires

**Alternative Options:**
- Use ESP32's USB port (5V from laptop)
- Use a 7805 linear regulator (less efficient, gets hot)
- Use a USB power bank (5V, 2A)

---

## Circuit 6: Temperature & Humidity Sensor (DHT22)

**Purpose:** Measure ambient temperature and humidity

```
DHT22 Sensor Pinout (left to right, front view):
┌────────────┐
│  DHT22     │
│ ┌────────┐ │
│ │        │ │
│ └────────┘ │
└─┬──┬──┬──┬─┘
  1  2  3  4
  │  │  │  │
  │  │  │  └─ NC (not connected)
  │  │  └──── GND → ESP32 GND
  │  └─────── DATA → ESP32 GPIO4 (with 10kΩ pull-up)
  └────────── VCC → ESP32 3.3V

Pull-up resistor (required):
ESP32 3.3V ──[10kΩ]── GPIO4 (DATA line)
```

**Component List:**
- 1× DHT22 sensor
- 1× 10kΩ resistor (pull-up)
- 3× jumper wires

**Code Library:**
```cpp
#include <DHT.h>
DHT dht(4, DHT22);
dht.begin();
float temp = dht.readTemperature(); // °C
float humidity = dht.readHumidity(); // %
```

---

## Circuit 7: Light Intensity Sensor (BH1750)

**Purpose:** Measure solar irradiance (lux) using digital I2C sensor

```
BH1750 Sensor (I2C)
┌────────────┐
│   BH1750   │
│  [●●●●●]   │  Light sensor window
└─┬──┬──┬──┬─┘
  │  │  │  │
  │  │  │  └─ ADDR (address select, leave floating or GND)
  │  │  └──── SCL → ESP32 GPIO22 (I2C Clock)
  │  └─────── SDA → ESP32 GPIO21 (I2C Data)
  └────────── VCC → ESP32 3.3V
             GND → ESP32 GND

I2C Address: 0x23 (default) or 0x5C (if ADDR → VCC)
```

**Component List:**
- 1× BH1750 digital light sensor module (GY-302)
- 4× jumper wires
- No pull-up resistors needed (already on module)

**Alternative (Cheaper):**
Use a simple LDR (Light Dependent Resistor):
```
ESP32 3.3V ──[10kΩ]──┬──> GPIO36 (ADC)
                      │
                    [LDR]
                      │
                     GND

Light level = analogRead(36);
// Higher value = brighter light
```

**Code Library:**
```cpp
#include <BH1750.h>
BH1750 lightMeter;
lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
float lux = lightMeter.readLightLevel();
```

---

## Circuit 8: LED Load Indicators

**Purpose:** Visual representation of building energy consumption

```
Building Load LEDs (3 buildings):

ESP32 GPIO25 ──[220Ω]──>|── (LED1, White) ──> GND
ESP32 GPIO26 ──[220Ω]──>|── (LED2, White) ──> GND
ESP32 GPIO27 ──[220Ω]──>|── (LED3, White) ──> GND

System Status LEDs:

ESP32 GPIO13 ──[220Ω]──>|── (LED4, Red, Grid Import) ──> GND
ESP32 GPIO15 ──[220Ω]──>|── (LED5, Green, Battery) ──> GND
ESP32 GPIO2  ──[220Ω]──>|── (LED6, Blue, Status) ──> GND

Current limiting calculation:
V_gpio = 3.3V
V_led = 2.0V (typical for white LED)
I_led = (3.3V - 2.0V) / 220Ω = 5.9mA (safe)

Using PWM for brightness control:
analogWrite(GPIO25, 128); // 50% brightness (0-255 scale)
```

**Component List:**
- 3× White LEDs (5mm, building loads)
- 1× Red LED (grid import indicator)
- 1× Green LED (battery indicator)
- 1× Blue LED (status indicator)
- 6× 220Ω resistors
- Jumper wires

---

## Complete Breadboard Layout

```
Breadboard Layout (Top View):

    Power Rails (Red/Blue lines on breadboard edges):
    [+] Rail: 5V from Buck Converter
    [-] Rail: GND (common ground)

    ┌─────────────────────────────────────────────────────────┐
    │ [+5V Rail]                                              │
    │                                                         │
    │  ESP32 DevKit (straddling center gap)                  │
    │  ┌─────────────────────────────────────┐               │
    │  │ USB              WiFi Antenna      │               │
    │  │ [○]                         [Chip] │               │
    │  │                                     │               │
    │  │ VIN·GND·GPIO34·35·32·4·21·22·...  │               │
    │  └──┬───┬───┬────┬──┬─┬──┬───┬────────┘               │
    │     │   │   │    │  │ │  │   │                        │
    │     5V  GND │    │  │ │  │   │                        │
    │             │    │  │ │  │   └──[BH1750 SCL]          │
    │             │    │  │ │  └──────[BH1750 SDA]          │
    │             │    │  │ └─────────[DHT22 DATA + 10kΩ]   │
    │             │    │  │                                  │
    │             │    │  └──[Battery Voltage Divider]      │
    │             │    │      22kΩ + 10kΩ                   │
    │             │    │                                     │
    │             │    └─────[Solar Current (ACS712 OUT)]   │
    │             │                                          │
    │             └──────────[Solar Voltage Divider]        │
    │                        10kΩ + 10kΩ                    │
    │                                                        │
    │  Sensor Modules (on right side of breadboard):        │
    │  - DHT22                                               │
    │  - BH1750                                              │
    │  - ACS712                                              │
    │                                                        │
    │  LED Array (on bottom rows):                          │
    │  GPIO25 ─[220Ω]─>|─GND  (Building 1)                  │
    │  GPIO26 ─[220Ω]─>|─GND  (Building 2)                  │
    │  GPIO27 ─[220Ω]─>|─GND  (Building 3)                  │
    │  GPIO13 ─[220Ω]─>|─GND  (Grid, Red)                   │
    │  GPIO15 ─[220Ω]─>|─GND  (Battery, Green)              │
    │                                                        │
    │ [GND Rail]                                             │
    └────────────────────────────────────────────────────────┘

External Components (not on breadboard):
- Solar Panel (wired to TP4056 or BMS)
- Battery Pack (in holder, wired to charger)
- Buck Converter (provides 5V to breadboard)
```

---

## Wiring Color Code Convention

For easier debugging, use consistent wire colors:

| Color | Purpose |
|-------|---------|
| **Red** | +5V or +3.3V power |
| **Black** | GND (ground) |
| **Yellow** | ADC signals (voltage measurements) |
| **Orange** | Analog sensor outputs (current, LDR) |
| **Green** | Digital I2C signals (SDA, SCL) |
| **Blue** | Digital GPIO (DHT22, LEDs) |
| **White** | Miscellaneous signals |

---

## Power Budget Analysis

Calculate total current draw to ensure battery life:

| Component | Voltage | Current | Power |
|-----------|---------|---------|-------|
| ESP32 (WiFi active) | 3.3V | 160mA | 528mW |
| DHT22 | 3.3V | 1.5mA | 5mW |
| BH1750 | 3.3V | 0.12mA | 0.4mW |
| ACS712 | 5V | 10mA | 50mW |
| 6× LEDs (max brightness) | 3.3V | 60mA | 200mW |
| **Total** | - | **~230mA** | **~780mW** |

**Battery Life Calculation:**
- Battery capacity: 2500mAh at 3.7V (per cell)
- 4S configuration: 2500mAh at 14.8V = 37Wh
- System draw: 0.78W
- Runtime: 37Wh / 0.78W = **47 hours** (continuous operation)

With solar charging during day:
- 10W solar panel produces ~6-8Wh per day (60-80% efficiency)
- System uses ~18.7Wh per day (24h × 0.78W)
- **Self-sufficient if sun available >3 hours/day**

---

## Safety Checklist

Before powering on:

- [ ] All voltage dividers use correct resistor values
- [ ] No short circuits between power rails
- [ ] Battery polarity correct (+ to +, - to -)
- [ ] ESP32 powered from 5V (not 14.8V directly!)
- [ ] All GND points connected to common ground
- [ ] Solar panel polarity correct
- [ ] LEDs have current-limiting resistors
- [ ] Battery voltage <16.8V (safe for Li-Ion)
- [ ] No loose wires touching adjacent pins
- [ ] Multimeter verified all voltages before connecting ESP32

---

## Troubleshooting Guide

### Problem: ESP32 doesn't boot
- Check 5V power supply with multimeter
- Try powering via USB (bypass buck converter)
- Press EN (reset) button

### Problem: ADC always reads 0 or 4095
- Check voltage divider resistors
- Measure voltage at ADC pin (should be <3.3V)
- Use multimeter to verify input voltage

### Problem: DHT22 returns NaN
- Check 10kΩ pull-up resistor on DATA line
- Verify VCC is 3.3V (not 5V)
- Wait 2 seconds after power-on before reading

### Problem: BH1750 not detected
- Check I2C wiring (SDA ↔ GPIO21, SCL ↔ GPIO22)
- Scan I2C bus: `Wire.begin(); Wire.beginTransmission(0x23);`
- Try alternate address 0x5C

### Problem: WiFi won't connect
- Check SSID and password in code
- Verify router is 2.4GHz (ESP32 doesn't support 5GHz)
- Move closer to router (signal strength)

### Problem: Battery drains quickly
- Reduce LED brightness (lower PWM duty cycle)
- Increase sampling interval (15s → 60s)
- Use deep sleep mode between readings

---

## Advanced: Deep Sleep for Battery Saving

To extend battery life, use ESP32 deep sleep:

```cpp
// After sending data
Serial.println("Going to sleep for 60 seconds...");
esp_sleep_enable_timer_wakeup(60 * 1000000); // 60 seconds in microseconds
esp_deep_sleep_start();

// ESP32 will reboot after 60 seconds
// Current draw: 10µA (vs 160mA active) = 16,000× reduction!
```

---

## Bill of Materials (BOM) Summary

### Full Hardware Prototype (Option A)

| Item | Qty | Unit Cost | Total |
|------|-----|-----------|-------|
| ESP32 DevKit v1 | 2 | ₹350 | ₹700 |
| Solar panel 5-10W | 1 | ₹500 | ₹500 |
| 18650 Li-Ion cells | 4 | ₹150 | ₹600 |
| 4S BMS charger board | 1 | ₹300 | ₹300 |
| LM2596 buck converter | 1 | ₹80 | ₹80 |
| ACS712 5A sensor | 2 | ₹80 | ₹160 |
| DHT22 sensor | 1 | ₹180 | ₹180 |
| BH1750 light sensor | 1 | ₹50 | ₹50 |
| LEDs (assorted) | 10 | ₹5 | ₹50 |
| Resistors (pack) | 1 | ₹50 | ₹50 |
| Breadboards | 2 | ₹50 | ₹100 |
| Jumper wires (pack) | 1 | ₹50 | ₹50 |
| Battery holder | 1 | ₹100 | ₹100 |
| Cardboard/craft supplies | - | ₹200 | ₹200 |
| **TOTAL** | - | - | **₹3,120** |

### Budget Demo (Option B)

| Item | Qty | Unit Cost | Total |
|------|-----|-----------|-------|
| ESP32 DevKit v1 | 1 | ₹350 | ₹350 |
| Potentiometers | 3 | ₹30 | ₹90 |
| LEDs | 10 | ₹5 | ₹50 |
| Resistors | 10 | ₹2 | ₹20 |
| Breadboard | 1 | ₹50 | ₹50 |
| Jumper wires | 1 | ₹50 | ₹50 |
| Cardboard model | - | ₹100 | ₹100 |
| **TOTAL** | - | - | **₹710** |

---

## Purchase Links (India)

**Online Stores:**
- Robu.in
- Amazon.in
- ElectronicComp.com
- Thinkrobotics.com
- Evelta.com

**Offline (Bangalore):**
- SP Road electronics market
- Naina Electronics
- Prime Electronics

**Offline (Delhi):**
- Lajpat Rai Market
- Nehru Place

**Offline (Mumbai):**
- Lamington Road
- Crawford Market

---

## Files in this Hardware Package

```
hardware/
├── circuit_diagrams.md          (this file)
├── esp32_firmware/
│   └── campus_energy_sensor.ino (ESP32 Arduino code)
├── esp32_data_receiver.py       (Python HTTP server)
└── README.md                    (setup instructions)
```

---

## Next Steps

1. **Order components** (2-3 days delivery)
2. **Test each circuit individually** before integration
3. **Upload firmware** to ESP32 using Arduino IDE
4. **Run Python server** to receive data
5. **Modify dashboard** to read from `live_sensor_data.json`
6. **Build physical model** (cardboard campus)
7. **Practice demo** and presentation

---

## Questions?

If you encounter issues:
1. Check the troubleshooting guide above
2. Verify wiring matches circuit diagrams
3. Use multimeter to test voltages
4. Test each sensor independently
5. Check serial monitor output (115200 baud)

**Good luck with your hackathon!** 🚀
