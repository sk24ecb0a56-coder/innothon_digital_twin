# Hardware Build Guide - Your Available Components

**Last Updated:** 2026-03-20

This guide shows you EXACTLY how to build the hardware prototype with the components you have.

---

## Your Components List

✅ **What you have:**
- 2× ESP32 WROOM 38-pin development boards
- 1× TP4056 charging module (Li-Ion charger, 1S)
- 1× 3S battery holder (for 3 batteries)
- 1× 1S battery holder (for 1 battery)
- Multiple resistors (various values)
- Capacitors
- Breadboards
- Jumper wires
- 4× 18650 Li-Ion batteries (assumed)

✅ **What you need to acquire (if not already have):**
- 1× DHT22 temperature sensor (₹180)
- 1× BH1750 light sensor OR LDR (₹50 or ₹5)
- 1× ACS712 5A current sensor module (₹80)
- 1× LM2596 buck converter module (₹80)
- 6× LEDs (various colors) (₹30)
- 6× 220Ω resistors for LEDs (₹12)
- Small solar panel 5-10W, 6-12V (₹500) OR potentiometer to simulate

**Total additional cost:** ₹400-900 depending on what you already have

---

## Battery Configuration: 3+1 Setup

Since you don't have a 4S holder, here's how to wire your 3+1 configuration:

```
┌─────────────────────────────────────────────────────┐
│  Battery Configuration (4S - Series Connection)     │
└─────────────────────────────────────────────────────┘

3S Battery Holder:
  [Cell 1]───[Cell 2]───[Cell 3]
     │          │          │
   (+)3.7V   (+)7.4V   (+)11.1V
   (─)        (─)        (─)

1S Battery Holder:
  [Cell 4]
     │
   (+)14.8V ← Final positive terminal
   (─)      ← Connect to Cell 3 negative

Wiring Steps:
1. Insert Cell 1, 2, 3 into 3S holder
2. Insert Cell 4 into 1S holder
3. Connect: Cell 3 negative (─) → Cell 4 negative (─) with wire
4. Connect: Cell 4 positive (+) → Cell 3 positive (+)
   NO! THIS IS WRONG - see below

CORRECT SERIES WIRING:
Battery Positive Terminal (+14.8V) = Cell 4 positive (+)
Battery Negative Terminal (GND)    = Cell 1 negative (─)

Step-by-step:
1. Cell 1 negative (─) → System GND (final negative terminal)
2. Cell 1 positive (+) → Cell 2 negative (─) [already in holder]
3. Cell 2 positive (+) → Cell 3 negative (─) [already in holder]
4. Cell 3 positive (+) → Cell 4 negative (─) [use wire jumper]
5. Cell 4 positive (+) → System +14.8V (final positive terminal)

Visual diagram:
┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐
│Cell 1│────→│Cell 2│────→│Cell 3│~~┐  │Cell 4│
│ 3.7V │     │ 3.7V │     │ 3.7V │  │  │ 3.7V │
└──┬───┘     └──────┘     └──────┘  │  └──┬───┘
   │                                 │     │
  GND                                └~~~~~┘
                                   (jumper wire)
                                        │
                                      +14.8V

~~~ = jumper wire connection
```

**Safety Notes:**
- ⚠️ Test voltage with multimeter: Should read ~14.8V (12-16.8V range)
- ⚠️ Never short circuit the terminals
- ⚠️ Use batteries with built-in protection (most 18650s have)
- ⚠️ Mark polarity clearly with tape/marker

---

## TP4056 Charging Setup

**Problem:** TP4056 is designed for **1S** (single 3.7V cell) charging only.
**Your battery pack:** 4S (14.8V) - too high for TP4056!

### Option A: Use TP4056 for Demonstration Only ❌ NOT RECOMMENDED

```
Solar Panel (6V max)
    │
    ├──[IN+]─┐
    │        │ TP4056 Module
    └──[IN-]─┤ (charges 1S only)
             │
   ┌──[B+]──┤
   │        │
   └──[B-]──┘
   │
   Single Cell (3.7V) for demo
```

This will only charge ONE battery, not your 4S pack.

### Option B: No Charging During Demo ✅ RECOMMENDED

**Best approach for hackathon:**
1. **Fully charge all 4 batteries** before the demo (using external charger)
2. **Don't use TP4056** during demonstration
3. Battery will last 40-50 hours on a charge (more than enough!)
4. Focus demo on energy management, not battery charging

### Option C: Buy a 4S BMS Module (₹300) ✅ IF TIME PERMITS

```
Solar Panel (14-18V)
    │
    ├──[IN+]─┐
    │        │ 4S BMS Charger Module
    └──[IN-]─┤ (balances all 4 cells)
             │
   ┌──[B1]──┤──→ Cell 1 (+)
   ├──[B2]──┤──→ Cell 2 (+)
   ├──[B3]──┤──→ Cell 3 (+)
   ├──[B4]──┤──→ Cell 4 (+)
   └──[B-]──┴──→ All cells (─)
```

Search for: "4S 14.8V Li-ion BMS charger module" on Amazon/Robu

---

## Complete Circuit Diagram for Your Setup

### ESP32 #1: Main Sensor Node

```
┌─────────────────────────────────────────────────────────┐
│                    POWER SUPPLY                         │
│                                                         │
│   Battery Pack (4S, 14.8V)                             │
│         │                                               │
│         ├──[IN+]─┐                                      │
│         │        │ LM2596 Buck Converter               │
│         └──[IN-]─┤ (Adjust to 5.0V output)             │
│                  │                                      │
│       ┌──[OUT+]─┤──→ ESP32 VIN (5V)                    │
│       │         │                                       │
│       └──[OUT-]─┴──→ ESP32 GND                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  VOLTAGE MEASUREMENTS                   │
│                                                         │
│  Solar Panel Voltage (if you have panel)               │
│  ┌─ Solar (+) [6-12V]                                  │
│  ├──[10kΩ]──┬──→ ESP32 GPIO34 (ADC)                    │
│  │          │                                           │
│  │      [10kΩ]                                          │
│  │          │                                           │
│  └──────────┴──→ GND                                    │
│                                                         │
│  OR Use Potentiometer to Simulate:                     │
│  ESP32 3.3V ──[10kΩ Pot]──┬──→ GPIO34                  │
│                            │                            │
│                           GND                           │
│                                                         │
│  Battery Voltage (4S monitoring)                       │
│  ┌─ Battery (+) [14.8V]                                │
│  ├──[22kΩ]──┬──→ ESP32 GPIO32 (ADC)                    │
│  │          │                                           │
│  │      [10kΩ]                                          │
│  │          │                                           │
│  └──────────┴──→ GND                                    │
│                                                         │
│  Divider ratio = 22+10 / 10 = 3.2                      │
│  Max voltage = 3.3V × 3.2 = 10.56V                     │
│  For 14.8V battery: ADC reads 14.8/3.2 = 4.625V        │
│  ⚠️ This exceeds 3.3V! Need adjustment!                │
│                                                         │
│  CORRECTED Battery Voltage Divider:                    │
│  ┌─ Battery (+) [14.8V]                                │
│  ├──[33kΩ]──┬──→ ESP32 GPIO32 (ADC)                    │
│  │          │    (or use 22kΩ + 10kΩ + 1kΩ = 33kΩ)    │
│  │      [10kΩ]                                          │
│  │          │                                           │
│  └──────────┴──→ GND                                    │
│                                                         │
│  New ratio = (33+10) / 10 = 4.3                        │
│  For 16.8V max: ADC = 16.8/4.3 = 3.9V                  │
│  Still too high! Use 47kΩ + 10kΩ:                      │
│  Ratio = 5.7, ADC = 16.8/5.7 = 2.95V ✓ SAFE           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                CURRENT MEASUREMENT                      │
│                                                         │
│  Solar Panel Current (if you have ACS712)              │
│  Solar (+) ───→ [ACS712 IP+]                           │
│                      │                                  │
│  Solar (─) ◄─── [ACS712 IP─]                           │
│                                                         │
│  [ACS712 Connections]                                  │
│  VCC (5V) ──→ ESP32 5V (from buck converter)          │
│  GND ──→ ESP32 GND                                     │
│  OUT ──→ ESP32 GPIO35 (ADC)                            │
│                                                         │
│  OR Simulate with Potentiometer:                      │
│  ESP32 3.3V ──[10kΩ Pot]──┬──→ GPIO35                  │
│                            │                            │
│                      Bias to 2.5V                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│             TEMPERATURE & LIGHT SENSORS                 │
│                                                         │
│  DHT22 Temperature Sensor                              │
│  ┌────────────┐                                         │
│  │   DHT22    │                                         │
│  └─┬──┬──┬──┬─┘                                         │
│    1  2  3  4                                           │
│    │  │  │  └─ NC                                       │
│    │  │  └──── GND → ESP32 GND                         │
│    │  └─────── DATA → ESP32 GPIO4 + [10kΩ pullup]     │
│    └────────── VCC → ESP32 3.3V                        │
│                                                         │
│  BH1750 Light Sensor (I2C)                             │
│  VCC ──→ ESP32 3.3V                                    │
│  GND ──→ ESP32 GND                                     │
│  SDA ──→ ESP32 GPIO21                                  │
│  SCL ──→ ESP32 GPIO22                                  │
│                                                         │
│  OR Use Simple LDR:                                    │
│  ESP32 3.3V ──[10kΩ]──┬──→ GPIO36 (ADC)               │
│                        │                                │
│                      [LDR]                             │
│                        │                                │
│                       GND                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   LED INDICATORS                        │
│                                                         │
│  Building Load LEDs (3 buildings)                      │
│  GPIO25 ──[220Ω]──>|── (White LED) ── GND             │
│  GPIO26 ──[220Ω]──>|── (White LED) ── GND             │
│  GPIO27 ──[220Ω]──>|── (White LED) ── GND             │
│                                                         │
│  System Status LEDs                                    │
│  GPIO13 ──[220Ω]──>|── (Red LED, Grid) ── GND         │
│  GPIO15 ──[220Ω]──>|── (Green LED, Batt) ── GND       │
│  GPIO2  ──[220Ω]──>|── (Blue LED, Status) ── GND      │
└─────────────────────────────────────────────────────────┘
```

### ESP32 #2: Backup/Display Node (Optional)

You have a second ESP32! Use it for:

**Option A: Display Node**
```
ESP32 #2 ──→ OLED Display (I2C)
         ├─→ More LEDs for visualization
         └─→ Buttons for manual control
```

**Option B: Second Sensor Location**
```
ESP32 #2 ──→ Monitor different building
         ──→ Sends data to same server
```

**Option C: Keep as Backup**
```
Just in case ESP32 #1 fails during demo!
```

---

## Simplified Budget Build (No Sensors)

If you don't have time to buy/wire sensors:

```
┌──────────────────────────────────────────────┐
│        DEMO MODE - Potentiometer Inputs      │
└──────────────────────────────────────────────┘

ESP32 Powered by USB from Laptop (5V)

Input Simulations:
1. Solar Power: Potentiometer on GPIO34
   ESP32 3.3V ──[10kΩ Pot]──┬──→ GPIO34
                             └──→ GND

2. Battery Level: Potentiometer on GPIO32
   ESP32 3.3V ──[10kΩ Pot]──┬──→ GPIO32
                             └──→ GND

3. Temperature: Fixed value in code (25°C)

4. Irradiance: Potentiometer on GPIO36
   ESP32 3.3V ──[10kΩ Pot]──┬──→ GPIO36
                             └──→ GND

LEDs (same as above):
- 3× White LEDs on GPIO25-27 (building loads)
- 1× Red LED on GPIO13 (grid import)
- 1× Green LED on GPIO15 (battery status)
- 1× Blue LED on GPIO2 (system status)

Total cost: ₹200 (LEDs, resistors, pots, breadboard)
Demo duration: Live adjustment with potentiometers!
```

---

## Assembly Steps

### Step 1: Battery Pack Assembly (15 minutes)

1. Insert 3 batteries into 3S holder
2. Insert 1 battery into 1S holder
3. Use multimeter to verify each cell: 3.0-4.2V ✓
4. Connect Cell 3 (+) to Cell 4 (─) with jumper wire
5. Measure total voltage: Should be 12-16.8V ✓
6. Label terminals clearly: RED for (+), BLACK for (─)

### Step 2: Buck Converter Setup (10 minutes)

1. Connect battery pack to LM2596 input (IN+, IN─)
2. **Before connecting ESP32**, adjust output:
   - Turn potentiometer while measuring output voltage
   - Set to exactly 5.0V (use multimeter)
   - Lock potentiometer with hot glue or tape
3. Connect output to breadboard power rails
4. Verify 5V with multimeter again

### Step 3: ESP32 Placement (5 minutes)

1. Place ESP32 straddling center gap of breadboard
2. Connect VIN to +5V rail
3. Connect GND to GND rail
4. Connect USB to laptop for programming
5. Press EN button to reset
6. LED should light up ✓

### Step 4: Voltage Dividers (20 minutes)

Build on breadboard:

**Battery Voltage Divider (GPIO32):**
```
Row 1: Battery (+) ── [47kΩ resistor] ── Row 2
Row 2: [Junction] ── Wire ── GPIO32
Row 2: [Junction] ── [10kΩ resistor] ── Row 3
Row 3: GND rail
```

**Solar Voltage Divider (GPIO34):** (if using solar panel)
```
Row 5: Solar (+) ── [10kΩ] ── Row 6
Row 6: [Junction] ── Wire ── GPIO34
Row 6: [Junction] ── [10kΩ] ── Row 7
Row 7: GND rail
```

Test each divider with multimeter before connecting to ESP32!

### Step 5: Sensors (30 minutes)

**DHT22:**
1. Insert into breadboard
2. VCC → 3.3V rail
3. GND → GND rail
4. DATA → GPIO4
5. Add 10kΩ resistor: 3.3V rail → GPIO4 (pull-up)

**BH1750 (or LDR):**
- BH1750: VCC→3.3V, GND→GND, SDA→GPIO21, SCL→GPIO22
- LDR: 3.3V → [10kΩ] → GPIO36 → [LDR] → GND

**ACS712 (if using):**
- VCC → 5V rail
- GND → GND rail
- OUT → GPIO35
- IP+/IP─ → in series with solar panel

### Step 6: LEDs (15 minutes)

For each LED:
1. Anode (long leg) → resistor → GPIO pin
2. Cathode (short leg) → GND rail

```
GPIO25 ──[220Ω]──→ LED1 (+) → (─) GND
GPIO26 ──[220Ω]──→ LED2 (+) → (─) GND
GPIO27 ──[220Ω]──→ LED3 (+) → (─) GND
GPIO13 ──[220Ω]──→ LED4 (+) → (─) GND (Red)
GPIO15 ──[220Ω]──→ LED5 (+) → (─) GND (Green)
GPIO2  ──[220Ω]──→ LED6 (+) → (─) GND (Blue)
```

### Step 7: Verification (10 minutes)

Before uploading code:

- [ ] All power connections secure
- [ ] No short circuits (use multimeter continuity test)
- [ ] Battery voltage correct (12-16.8V)
- [ ] 5V rail measures 5.0V
- [ ] 3.3V pin on ESP32 measures 3.3V
- [ ] All voltage dividers tested
- [ ] LED polarity correct (long leg to resistor)
- [ ] No loose wires

---

## Firmware Upload

### Install Arduino IDE

1. Download from: https://www.arduino.cc/en/software
2. Install ESP32 board support:
   - File → Preferences
   - Additional Board URLs:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install

### Install Libraries

Tools → Manage Libraries → Install:
- DHT sensor library (by Adafruit)
- BH1750 (by Christopher Laws)
- ArduinoJson (by Benoit Blanchon)

### Upload Code

1. Open: `hardware/esp32_firmware/campus_energy_sensor.ino`
2. Edit WiFi credentials (lines 29-30):
   ```cpp
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASSWORD = "YourPassword";
   ```
3. Edit server URL (line 33):
   ```cpp
   const char* SERVER_URL = "http://192.168.1.XXX:5000/api/sensor-data";
   ```
   Replace XXX with your laptop IP address
4. Select: Tools → Board → ESP32 Dev Module
5. Select: Tools → Port → COM3 (or your ESP32 port)
6. Click Upload (→) button
7. Wait for "Done uploading"
8. Open Serial Monitor (115200 baud)
9. You should see sensor readings every 15 seconds!

---

## Physical Model (Optional)

Build a cardboard campus model:

```
┌────────────────────────────────────┐
│    Cardboard Campus Layout         │
│                                    │
│  ┌─────┐  ┌─────┐  ┌─────┐        │
│  │LED 1│  │LED 2│  │LED 3│  ←─ Building LEDs
│  │Bldg1│  │Bldg2│  │Bldg3│        │
│  └─────┘  └─────┘  └─────┘        │
│                                    │
│  ┌──────────┐                      │
│  │ Solar    │  ←─ Solar panel or cardboard + foil
│  │ Panels   │                      │
│  └──────────┘                      │
│                                    │
│  [Battery]  [ESP32]  [Sensors]     │
│   ←──┴───────┴─────────┴────       │
│   Mounted on base                  │
└────────────────────────────────────┘

Materials:
- Cardboard (₹50)
- White paper (₹20)
- Markers/colors (₹50)
- Glue/tape (₹30)
- Aluminum foil for solar panels (₹20)

Total: ₹170
```

---

## Testing Checklist

Before demo day:

- [ ] ESP32 connects to WiFi successfully
- [ ] Serial monitor shows sensor readings every 15 seconds
- [ ] Flask server receives POST requests (check terminal)
- [ ] Dashboard displays live data
- [ ] Battery lasts >4 hours on full charge
- [ ] All LEDs working (brightness varies with load)
- [ ] Temperature reading realistic (20-30°C)
- [ ] Battery voltage shows correct value (14.8V)
- [ ] Solar input adjustable (pot or panel)
- [ ] No overheating components
- [ ] Physical model secure and presentable
- [ ] Backup ESP32 programmed (just in case!)

---

## What If Things Break?

**WiFi won't connect:**
- Switch to mobile hotspot
- Check SSID/password in code
- Move closer to router

**Sensor reads NaN:**
- Use simulated values (already in code as fallback)
- Demo still works with simulated data!

**Battery dies:**
- Use USB power (5V) instead
- Disconnect battery, power via laptop

**ESP32 bricked:**
- Use second ESP32 (that's why you have 2!)
- Hold BOOT button while uploading

**No time for hardware:**
- Run dashboard with simulated data only
- Still impressive! AI models work the same

---

## Next Steps

1. ✅ Read this guide thoroughly
2. ✅ Acquire missing components (1-2 days)
3. ✅ Build power supply circuit first (test with multimeter)
4. ✅ Add ESP32 and test with simple LED blink
5. ✅ Add sensors one by one, test each
6. ✅ Upload firmware and test WiFi
7. ✅ Run Python server and dashboard
8. ✅ Build physical model
9. ✅ Practice demo presentation
10. ✅ Win hackathon! 🏆

---

**Questions?** Check `hardware/CIRCUIT_DIAGRAMS.md` for detailed circuit schematics.

**Good luck!** 🚀
