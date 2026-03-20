"""
Database Layer for Campus Energy Digital Twin.

Provides persistent storage for sensor readings, predictions, and anomalies.
Uses SQLite for simplicity and portability (no server required).
"""

from __future__ import annotations

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import json


class SensorDatabase:
    """
    SQLite database manager for sensor data storage.

    Features:
    - Automatic table creation
    - Sensor readings storage
    - Time-series queries
    - Data retention management
    - Export to pandas DataFrame
    """

    def __init__(self, db_path: str = "sensor_data.db"):
        """
        Initialize database connection.

        Parameters
        ----------
        db_path : str
            Path to SQLite database file. Created if doesn't exist.
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Main sensor readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
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
            )
        """)

        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
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
            )
        """)

        # System KPIs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                total_demand_kwh REAL NOT NULL,
                total_solar_kwh REAL NOT NULL,
                total_grid_import_kwh REAL NOT NULL,
                total_grid_export_kwh REAL NOT NULL,
                self_sufficiency_pct REAL NOT NULL,
                solar_fraction_pct REAL NOT NULL,
                cost_savings_inr REAL NOT NULL,
                avg_battery_soc_pct REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON sensor_readings(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomaly
            ON sensor_readings(is_anomaly)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prediction_timestamp
            ON predictions(timestamp)
        """)

        self.conn.commit()

    def insert_reading(self, reading: Dict[str, Any]) -> int:
        """
        Insert a single sensor reading.

        Parameters
        ----------
        reading : dict
            Sensor reading data with keys matching table columns.

        Returns
        -------
        int
            ID of inserted row.
        """
        cursor = self.conn.cursor()

        # Convert timestamp if it's an integer (milliseconds)
        if isinstance(reading.get('timestamp'), (int, float)):
            timestamp = datetime.fromtimestamp(reading['timestamp'] / 1000.0)
        else:
            timestamp = reading.get('timestamp', datetime.now())

        cursor.execute("""
            INSERT INTO sensor_readings (
                timestamp, solar_gen_kw, solar_voltage, solar_current,
                battery_voltage, battery_soc_pct, temperature_c,
                irradiance_lux, irradiance_norm, demand_kw,
                grid_import_kw, grid_export_kw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            reading.get('solar_gen_kw', 0.0),
            reading.get('solar_voltage'),
            reading.get('solar_current'),
            reading.get('battery_voltage', 14.8),
            reading.get('battery_soc_pct', 50.0),
            reading.get('temperature_c', 25.0),
            reading.get('irradiance_lux'),
            reading.get('irradiance_norm'),
            reading.get('demand_kw', 0.0),
            reading.get('grid_import_kw'),
            reading.get('grid_export_kw')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent sensor reading.

        Returns
        -------
        dict or None
            Latest reading as dictionary, or None if no data.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_readings(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Query sensor readings within time range.

        Parameters
        ----------
        start_time : datetime, optional
            Start of time range. Default is 90 days ago.
        end_time : datetime, optional
            End of time range. Default is now.
        limit : int, optional
            Maximum number of rows to return.

        Returns
        -------
        pd.DataFrame
            Sensor readings as DataFrame.
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=90)
        if end_time is None:
            end_time = datetime.now()

        query = """
            SELECT * FROM sensor_readings
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(
            query,
            self.conn,
            params=(start_time, end_time),
            parse_dates=['timestamp', 'created_at']
        )

        return df

    def get_anomalies(self, days: int = 7) -> pd.DataFrame:
        """
        Get all anomalies from last N days.

        Parameters
        ----------
        days : int
            Number of days to look back.

        Returns
        -------
        pd.DataFrame
            Anomaly records.
        """
        start_time = datetime.now() - timedelta(days=days)

        query = """
            SELECT * FROM sensor_readings
            WHERE is_anomaly = 1 AND timestamp > ?
            ORDER BY anomaly_score DESC
        """

        df = pd.read_sql_query(
            query,
            self.conn,
            params=(start_time,),
            parse_dates=['timestamp']
        )

        return df

    def update_anomaly(self, reading_id: int, is_anomaly: bool,
                      anomaly_score: float, anomaly_type: str):
        """
        Update anomaly status for a reading.

        Parameters
        ----------
        reading_id : int
            ID of reading to update.
        is_anomaly : bool
            Whether reading is an anomaly.
        anomaly_score : float
            Anomaly score from detector.
        anomaly_type : str
            Type of anomaly (e.g., "demand_spike").
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sensor_readings
            SET is_anomaly = ?, anomaly_score = ?, anomaly_type = ?
            WHERE id = ?
        """, (int(is_anomaly), anomaly_score, anomaly_type, reading_id))

        self.conn.commit()

    def insert_prediction(self, prediction: Dict[str, Any]) -> int:
        """
        Insert a prediction record.

        Parameters
        ----------
        prediction : dict
            Prediction data.

        Returns
        -------
        int
            ID of inserted row.
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO predictions (
                timestamp, prediction_horizon_hours,
                predicted_demand_kw, predicted_solar_kw,
                actual_demand_kw, actual_solar_kw
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            prediction.get('timestamp', datetime.now()),
            prediction['horizon_hours'],
            prediction['predicted_demand_kw'],
            prediction['predicted_solar_kw'],
            prediction.get('actual_demand_kw'),
            prediction.get('actual_solar_kw')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def insert_daily_kpis(self, kpis: Dict[str, Any]) -> int:
        """
        Insert daily KPI summary.

        Parameters
        ----------
        kpis : dict
            Daily KPI values.

        Returns
        -------
        int
            ID of inserted row.
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO system_kpis (
                date, total_demand_kwh, total_solar_kwh,
                total_grid_import_kwh, total_grid_export_kwh,
                self_sufficiency_pct, solar_fraction_pct,
                cost_savings_inr, avg_battery_soc_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kpis.get('date', datetime.now().date()),
            kpis['total_demand_kwh'],
            kpis['total_solar_kwh'],
            kpis['total_grid_import_kwh'],
            kpis['total_grid_export_kwh'],
            kpis['self_sufficiency_pct'],
            kpis['solar_fraction_pct'],
            kpis['cost_savings_inr'],
            kpis['avg_battery_soc_pct']
        ))

        self.conn.commit()
        return cursor.lastrowid

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Delete data older than specified days.

        Parameters
        ----------
        days_to_keep : int
            Number of days of data to retain.
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cursor = self.conn.cursor()

        cursor.execute("""
            DELETE FROM sensor_readings
            WHERE timestamp < ?
        """, (cutoff_date,))

        cursor.execute("""
            DELETE FROM predictions
            WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_readings = cursor.rowcount
        self.conn.commit()

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        return deleted_readings

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns
        -------
        dict
            Statistics about database contents.
        """
        cursor = self.conn.cursor()

        # Count total readings
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        total_readings = cursor.fetchone()[0]

        # Count anomalies
        cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE is_anomaly = 1")
        total_anomalies = cursor.fetchone()[0]

        # Get date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM sensor_readings
        """)
        min_date, max_date = cursor.fetchone()

        # Get database file size
        db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0

        return {
            'total_readings': total_readings,
            'total_anomalies': total_anomalies,
            'anomaly_rate_pct': (total_anomalies / total_readings * 100) if total_readings > 0 else 0,
            'earliest_reading': min_date,
            'latest_reading': max_date,
            'database_size_mb': db_size_mb,
            'database_path': self.db_path
        }

    def export_to_csv(self, output_path: str, days: int = 30):
        """
        Export recent data to CSV file.

        Parameters
        ----------
        output_path : str
            Path to output CSV file.
        days : int
            Number of days to export.
        """
        df = self.get_readings(
            start_time=datetime.now() - timedelta(days=days)
        )
        df.to_csv(output_path, index=False)
        return len(df)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for common operations

def get_database(db_path: str = "sensor_data.db") -> SensorDatabase:
    """
    Get database instance.

    Parameters
    ----------
    db_path : str
        Path to database file.

    Returns
    -------
    SensorDatabase
        Database instance.
    """
    return SensorDatabase(db_path)


def load_historical_data(days: int = 90, db_path: str = "sensor_data.db") -> pd.DataFrame:
    """
    Load historical data from database.

    Parameters
    ----------
    days : int
        Number of days to load.
    db_path : str
        Path to database file.

    Returns
    -------
    pd.DataFrame
        Historical sensor data.
    """
    with SensorDatabase(db_path) as db:
        df = db.get_readings(
            start_time=datetime.now() - timedelta(days=days)
        )
    return df


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("Campus Energy Digital Twin - Database Layer Demo")
    print("=" * 60)

    # Create database
    db = SensorDatabase()

    # Insert sample reading
    sample_reading = {
        'timestamp': datetime.now(),
        'solar_gen_kw': 0.245,
        'solar_voltage': 8.3,
        'solar_current': 0.03,
        'battery_voltage': 14.2,
        'battery_soc_pct': 65.5,
        'temperature_c': 27.3,
        'irradiance_lux': 45230,
        'irradiance_norm': 0.452,
        'demand_kw': 0.387,
        'grid_import_kw': 0.142,
        'grid_export_kw': 0.0
    }

    reading_id = db.insert_reading(sample_reading)
    print(f"\n✓ Inserted sample reading (ID: {reading_id})")

    # Get latest reading
    latest = db.get_latest_reading()
    print(f"\n✓ Latest reading:")
    print(f"  - Timestamp: {latest['timestamp']}")
    print(f"  - Solar: {latest['solar_gen_kw']} kW")
    print(f"  - Battery: {latest['battery_soc_pct']}%")
    print(f"  - Demand: {latest['demand_kw']} kW")

    # Get database stats
    stats = db.get_stats()
    print(f"\n✓ Database statistics:")
    print(f"  - Total readings: {stats['total_readings']}")
    print(f"  - Total anomalies: {stats['total_anomalies']}")
    print(f"  - Database size: {stats['database_size_mb']:.2f} MB")
    print(f"  - Path: {stats['database_path']}")

    db.close()
    print("\n✓ Database closed successfully")
    print("\nDatabase ready for use! 🚀")
