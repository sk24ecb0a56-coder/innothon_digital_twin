"""
Simple HTTP Server to receive live sensor data from ESP32.

Run this alongside the Streamlit dashboard to enable live hardware data.

Usage:
    python hardware/esp32_data_receiver.py

The server will:
1. Listen on http://0.0.0.0:5000/api/sensor-data
2. Receive JSON data from ESP32
3. Store latest reading in a JSON file AND SQLite database
4. Dashboard can read from database for historical analysis
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.database import SensorDatabase

app = Flask(__name__)

# Path to store latest sensor reading (for backward compatibility)
DATA_FILE = "live_sensor_data.json"

# Database for persistent storage
db = SensorDatabase("sensor_data.db")

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from ESP32 and save to file + database."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        # Add server timestamp
        data['server_timestamp'] = datetime.now().isoformat()

        # Save to file (overwrite previous reading) - for backward compatibility
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        # Save to database for persistent storage
        try:
            reading_id = db.insert_reading(data)
            print(f"✓ Received data at {data['server_timestamp']} (DB ID: {reading_id})")
        except Exception as db_error:
            print(f"⚠️  Database insert failed: {db_error}")
            print(f"✓ Received data at {data['server_timestamp']} (file only)")

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
    try:
        db_stats = db.get_stats()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_available": os.path.exists(DATA_FILE),
            "database": {
                "total_readings": db_stats['total_readings'],
                "total_anomalies": db_stats['total_anomalies'],
                "database_size_mb": db_stats['database_size_mb']
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        stats = db.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ESP32 Data Receiver Server (with Database)")
    print("="*60)
    print("\nServer starting on http://0.0.0.0:5000")
    print("\nEndpoints:")
    print("  POST /api/sensor-data  - Receive sensor data from ESP32")
    print("  GET  /api/sensor-data  - Get latest sensor reading")
    print("  GET  /health           - Health check + DB stats")
    print("  GET  /api/stats        - Database statistics")

    # Show database info
    try:
        stats = db.get_stats()
        print(f"\nDatabase Status:")
        print(f"  Path: {stats['database_path']}")
        print(f"  Total readings: {stats['total_readings']}")
        print(f"  Size: {stats['database_size_mb']:.2f} MB")
    except Exception as e:
        print(f"\n⚠️  Database initialization warning: {e}")

    print("\nWaiting for ESP32 connections...")
    print("="*60 + "\n")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        # Close database on shutdown
        db.close()
        print("\n✓ Database closed cleanly")
