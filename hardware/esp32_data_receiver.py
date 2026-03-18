"""
Simple HTTP Server to receive live sensor data from ESP32.

Run this alongside the Streamlit dashboard to enable live hardware data.

Usage:
    python hardware/esp32_data_receiver.py

The server will:
1. Listen on http://0.0.0.0:5000/api/sensor-data
2. Receive JSON data from ESP32
3. Store latest reading in a JSON file
4. Dashboard can read this file for live data
"""

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Path to store latest sensor reading
DATA_FILE = "live_sensor_data.json"

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from ESP32 and save to file."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        # Add server timestamp
        data['server_timestamp'] = datetime.now().isoformat()

        # Save to file (overwrite previous reading)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Received data at {data['server_timestamp']}")
        print(f"  Solar: {data.get('solar_gen_kw', 0):.3f} kW")
        print(f"  Demand: {data.get('demand_kw', 0):.3f} kW")
        print(f"  Battery SoC: {data.get('battery_soc_pct', 0):.1f} %")
        print()

        return jsonify({"status": "success", "message": "Data received"}), 200

    except Exception as e:
        print(f"✗ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensor-data', methods=['GET'])
def get_latest_data():
    """Retrieve the latest sensor reading."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return jsonify(data), 200
        else:
            return jsonify({"error": "No data available yet"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_available": os.path.exists(DATA_FILE)
    }), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ESP32 Data Receiver Server")
    print("="*60)
    print("\nServer starting on http://0.0.0.0:5000")
    print("\nEndpoints:")
    print("  POST /api/sensor-data  - Receive sensor data from ESP32")
    print("  GET  /api/sensor-data  - Get latest sensor reading")
    print("  GET  /health           - Health check")
    print("\nWaiting for ESP32 connections...")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False)
