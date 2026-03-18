/*
 * Campus Energy Digital Twin - ESP32 Sensor Node
 *
 * Reads sensors and sends data to the digital twin dashboard via HTTP POST
 *
 * Hardware Connections:
 * - GPIO34 (ADC1_CH6): Solar voltage (via voltage divider)
 * - GPIO35 (ADC1_CH7): Solar current (ACS712 output)
 * - GPIO32 (ADC1_CH4): Battery voltage (via voltage divider)
 * - GPIO4: DHT22 temperature sensor (data pin)
 * - GPIO21: I2C SDA (for BH1750 light sensor)
 * - GPIO22: I2C SCL (for BH1750 light sensor)
 * - GPIO25-27: LED outputs for building loads
 * - GPIO13-15: LED indicators (grid, battery, status)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Wire.h>
#include <BH1750.h>
#include <ArduinoJson.h>

// ============================================================================
// CONFIGURATION - MODIFY THESE FOR YOUR SETUP
// ============================================================================

// WiFi credentials
const char* WIFI_SSID = "YourWiFiName";
const char* WIFI_PASSWORD = "YourWiFiPassword";

// Server endpoint (update with your laptop IP)
const char* SERVER_URL = "http://192.168.1.100:5000/api/sensor-data";

// System parameters
const float SOLAR_CAPACITY_KW = 0.300;  // 300W solar panel = 0.3 kW
const float BATTERY_CAPACITY_KWH = 0.5; // 500Wh battery pack = 0.5 kWh

// Sensor calibration factors
const float SOLAR_VOLTAGE_DIVIDER = 2.0;      // 10kΩ + 10kΩ divider
const float BATTERY_VOLTAGE_DIVIDER = 3.2;    // 22kΩ + 10kΩ divider
const float ACS712_SENSITIVITY = 0.185;       // 185mV per amp (5A version)
const float ACS712_ZERO_CURRENT = 2.5;        // 2.5V at 0A

// Pin definitions
#define SOLAR_VOLTAGE_PIN 34
#define SOLAR_CURRENT_PIN 35
#define BATTERY_VOLTAGE_PIN 32
#define DHT_PIN 4
#define LED_BUILDING1_PIN 25
#define LED_BUILDING2_PIN 26
#define LED_BUILDING3_PIN 27
#define LED_GRID_PIN 13
#define LED_BATTERY_PIN 15
#define LED_STATUS_PIN 2  // Built-in LED

// Sampling interval
const unsigned long SAMPLE_INTERVAL_MS = 15000; // 15 seconds

// ============================================================================
// GLOBAL OBJECTS
// ============================================================================

DHT dht(DHT_PIN, DHT22);
BH1750 lightMeter;
unsigned long lastSampleTime = 0;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n====================================");
  Serial.println("Campus Energy Digital Twin - ESP32");
  Serial.println("====================================\n");

  // Initialize GPIO pins
  pinMode(LED_STATUS_PIN, OUTPUT);
  pinMode(LED_GRID_PIN, OUTPUT);
  pinMode(LED_BATTERY_PIN, OUTPUT);
  pinMode(LED_BUILDING1_PIN, OUTPUT);
  pinMode(LED_BUILDING2_PIN, OUTPUT);
  pinMode(LED_BUILDING3_PIN, OUTPUT);

  // Initialize sensors
  Serial.println("Initializing sensors...");
  dht.begin();

  Wire.begin(21, 22); // SDA, SCL
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("✓ BH1750 light sensor initialized");
  } else {
    Serial.println("✗ BH1750 not found (will use simulated values)");
  }

  // Connect to WiFi
  connectWiFi();

  Serial.println("\nSystem ready. Starting data collection...\n");
  blinkLED(LED_STATUS_PIN, 3); // Signal ready
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  unsigned long currentTime = millis();

  // Sample sensors at regular intervals
  if (currentTime - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = currentTime;

    // Read all sensors
    SensorData data = readSensors();

    // Print to serial for debugging
    printSensorData(data);

    // Send to server
    sendDataToServer(data);

    // Update LED indicators
    updateLEDs(data);

    // Blink status LED
    digitalWrite(LED_STATUS_PIN, HIGH);
    delay(100);
    digitalWrite(LED_STATUS_PIN, LOW);
  }

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }

  delay(100);
}

// ============================================================================
// SENSOR DATA STRUCTURE
// ============================================================================

struct SensorData {
  float solarGenKW;
  float solarVoltage;
  float solarCurrent;
  float batteryVoltage;
  float batterySOC;
  float temperatureC;
  float irradianceLux;
  float irradianceNorm;
  float demandKW;
  float gridImportKW;
};

// ============================================================================
// SENSOR READING FUNCTIONS
// ============================================================================

SensorData readSensors() {
  SensorData data;

  // Read solar panel voltage
  int solarVoltageRaw = analogRead(SOLAR_VOLTAGE_PIN);
  data.solarVoltage = (solarVoltageRaw / 4095.0) * 3.3 * SOLAR_VOLTAGE_DIVIDER;

  // Read solar panel current
  int solarCurrentRaw = analogRead(SOLAR_CURRENT_PIN);
  float solarCurrentVoltage = (solarCurrentRaw / 4095.0) * 3.3;
  data.solarCurrent = (solarCurrentVoltage - ACS712_ZERO_CURRENT) / ACS712_SENSITIVITY;

  // Clamp negative current to zero
  if (data.solarCurrent < 0) {
    data.solarCurrent = 0;
  }

  // Calculate solar power
  data.solarGenKW = (data.solarVoltage * data.solarCurrent) / 1000.0;

  // Read battery voltage
  int batteryVoltageRaw = analogRead(BATTERY_VOLTAGE_PIN);
  data.batteryVoltage = (batteryVoltageRaw / 4095.0) * 3.3 * BATTERY_VOLTAGE_DIVIDER;

  // Estimate battery SOC (simple linear approximation)
  // For 4S Li-Ion: 16.8V = 100%, 12.0V = 0%
  float batterySOCPercent = ((data.batteryVoltage - 12.0) / (16.8 - 12.0)) * 100.0;
  data.batterySOC = constrain(batterySOCPercent, 0.0, 100.0);

  // Read temperature
  data.temperatureC = dht.readTemperature();
  if (isnan(data.temperatureC)) {
    data.temperatureC = 25.0; // Default if DHT22 fails
  }

  // Read light intensity
  data.irradianceLux = lightMeter.readLightLevel();
  if (data.irradianceLux < 0 || isnan(data.irradianceLux)) {
    data.irradianceLux = 0.0; // Default if BH1750 fails
  }

  // Normalize irradiance (0-1 scale)
  // Full sunlight ≈ 100,000 lux
  data.irradianceNorm = constrain(data.irradianceLux / 100000.0, 0.0, 1.0);

  // Simulate campus demand based on time of day
  data.demandKW = simulateCampusDemand();

  // Calculate grid import (if demand > solar)
  data.gridImportKW = max(0.0f, data.demandKW - data.solarGenKW);

  return data;
}

// ============================================================================
// CAMPUS DEMAND SIMULATION
// ============================================================================

float simulateCampusDemand() {
  // Get current time
  time_t now;
  struct tm timeinfo;
  time(&now);
  localtime_r(&now, &timeinfo);

  float hour = timeinfo.tm_hour + timeinfo.tm_min / 60.0;
  bool isWeekend = (timeinfo.tm_wday == 0 || timeinfo.tm_wday == 6);

  // Base and peak demand
  float baseKW = 0.2;  // 200W base load
  float peakKW = 0.5;  // 500W peak load

  if (isWeekend) {
    // Flatter weekend profile
    if (hour >= 8 && hour <= 18) {
      return baseKW + 0.3 * (peakKW - baseKW) * sin(PI * (hour - 8) / 10);
    }
    return baseKW * 0.6;
  }

  // Weekday profile
  if (hour < 7) {
    return baseKW * 0.7;
  } else if (hour >= 7 && hour < 9) {
    return baseKW + (peakKW - baseKW) * (hour - 7) / 2;
  } else if (hour >= 9 && hour < 12) {
    return peakKW;
  } else if (hour >= 12 && hour < 14) {
    return peakKW * 0.85; // Lunch dip
  } else if (hour >= 14 && hour < 18) {
    return peakKW;
  } else if (hour >= 18 && hour < 22) {
    return baseKW + (peakKW - baseKW) * (22 - hour) / 4;
  } else {
    return baseKW * 0.7;
  }
}

// ============================================================================
// NETWORK FUNCTIONS
// ============================================================================

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi connection failed");
  }
}

void sendDataToServer(SensorData data) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot send data - WiFi not connected");
    return;
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  // Create JSON payload
  StaticJsonDocument<512> doc;
  doc["timestamp"] = millis();
  doc["solar_gen_kw"] = round(data.solarGenKW * 100) / 100.0;
  doc["solar_voltage"] = round(data.solarVoltage * 10) / 10.0;
  doc["solar_current"] = round(data.solarCurrent * 100) / 100.0;
  doc["battery_voltage"] = round(data.batteryVoltage * 10) / 10.0;
  doc["battery_soc_pct"] = round(data.batterySOC * 10) / 10.0;
  doc["temperature_c"] = round(data.temperatureC * 10) / 10.0;
  doc["irradiance_lux"] = round(data.irradianceLux);
  doc["irradiance_norm"] = round(data.irradianceNorm * 1000) / 1000.0;
  doc["demand_kw"] = round(data.demandKW * 100) / 100.0;
  doc["grid_import_kw"] = round(data.gridImportKW * 100) / 100.0;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  // Send HTTP POST
  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    Serial.print("✓ Data sent. HTTP ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("✗ HTTP POST failed: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}

// ============================================================================
// LED INDICATOR FUNCTIONS
// ============================================================================

void updateLEDs(SensorData data) {
  // Grid import LED (red) - brightness proportional to import
  int gridBrightness = constrain(map(data.gridImportKW * 1000, 0, 500, 0, 255), 0, 255);
  analogWrite(LED_GRID_PIN, gridBrightness);

  // Battery LED (green) - brightness proportional to SOC
  int batteryBrightness = constrain(map(data.batterySOC, 0, 100, 0, 255), 0, 255);
  analogWrite(LED_BATTERY_PIN, batteryBrightness);

  // Building LEDs - simulate load with PWM
  int buildingBrightness = constrain(map(data.demandKW * 1000, 0, 500, 0, 255), 0, 255);
  analogWrite(LED_BUILDING1_PIN, buildingBrightness);
  analogWrite(LED_BUILDING2_PIN, buildingBrightness * 0.8);
  analogWrite(LED_BUILDING3_PIN, buildingBrightness * 0.6);
}

void blinkLED(int pin, int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(200);
    digitalWrite(pin, LOW);
    delay(200);
  }
}

// ============================================================================
// DEBUG FUNCTIONS
// ============================================================================

void printSensorData(SensorData data) {
  Serial.println("─────────────────────────────────────");
  Serial.print("Solar: ");
  Serial.print(data.solarGenKW * 1000, 1);
  Serial.print(" W (");
  Serial.print(data.solarVoltage, 1);
  Serial.print(" V × ");
  Serial.print(data.solarCurrent, 2);
  Serial.println(" A)");

  Serial.print("Battery: ");
  Serial.print(data.batteryVoltage, 1);
  Serial.print(" V (SoC: ");
  Serial.print(data.batterySOC, 1);
  Serial.println(" %)");

  Serial.print("Temperature: ");
  Serial.print(data.temperatureC, 1);
  Serial.println(" °C");

  Serial.print("Irradiance: ");
  Serial.print(data.irradianceLux, 0);
  Serial.print(" lux (norm: ");
  Serial.print(data.irradianceNorm, 3);
  Serial.println(")");

  Serial.print("Demand: ");
  Serial.print(data.demandKW * 1000, 1);
  Serial.println(" W");

  Serial.print("Grid Import: ");
  Serial.print(data.gridImportKW * 1000, 1);
  Serial.println(" W");
}
