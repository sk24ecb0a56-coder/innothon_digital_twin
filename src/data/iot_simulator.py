"""
IoT Data Simulator for Campus Energy Systems.

Generates realistic synthetic sensor data for:
- Solar PV generation
- Campus energy demand (building loads)
- Battery storage state
- Ambient temperature and irradiance
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


RANDOM_SEED = 42

# Cloud cover simulation parameters
CLOUD_MEAN = 0.2          # Mean cloud attenuation fraction
CLOUD_STD = 0.15          # Standard deviation of cloud attenuation
MIN_CLOUD_FACTOR = 0.1    # Minimum cloud transmission factor (heavily overcast)
MAX_CLOUD_FACTOR = 1.0    # Maximum cloud transmission factor (clear sky)


def _solar_irradiance(hour: float, cloud_factor: float = 1.0) -> float:
    """Return normalised solar irradiance (0-1) for a given hour of day."""
    if hour < 6 or hour > 20:
        return 0.0
    peak = np.sin(np.pi * (hour - 6) / 14) * cloud_factor
    return max(0.0, float(peak))


def _campus_load_kw(
    hour: float,
    is_weekend: bool,
    base_kw: float = 200.0,
    peak_kw: float = 500.0,
) -> float:
    """Return campus energy demand (kW) for a given hour."""
    if is_weekend:
        # Lower, flatter profile on weekends
        if 8 <= hour <= 18:
            return base_kw + 0.3 * (peak_kw - base_kw) * np.sin(np.pi * (hour - 8) / 10)
        return base_kw * 0.6
    # Weekday profile: morning ramp + lunch dip + afternoon peak
    if hour < 7:
        return base_kw * 0.7
    elif 7 <= hour < 9:
        return base_kw + (peak_kw - base_kw) * (hour - 7) / 2
    elif 9 <= hour < 12:
        return peak_kw
    elif 12 <= hour < 14:
        return peak_kw * 0.85  # lunch dip
    elif 14 <= hour < 18:
        return peak_kw
    elif 18 <= hour < 22:
        return base_kw + (peak_kw - base_kw) * (22 - hour) / 4
    else:
        return base_kw * 0.7


def generate_iot_data(
    start_date: str = "2024-01-01",
    days: int = 90,
    interval_minutes: int = 15,
    solar_capacity_kw: float = 300.0,
    battery_capacity_kwh: float = 500.0,
    random_seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate synthetic IoT sensor data for a campus energy system.

    Parameters
    ----------
    start_date : str
        ISO date string for the first timestamp.
    days : int
        Number of days to simulate.
    interval_minutes : int
        Sampling interval in minutes.
    solar_capacity_kw : float
        Installed peak solar capacity in kW.
    battery_capacity_kwh : float
        Battery storage capacity in kWh.
    random_seed : int
        Seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Timestamped sensor readings.
    """
    rng = np.random.default_rng(random_seed)

    start = datetime.fromisoformat(start_date)
    steps = int(days * 24 * 60 / interval_minutes)
    timestamps = [start + timedelta(minutes=i * interval_minutes) for i in range(steps)]

    records = []
    battery_soc = 0.5 * battery_capacity_kwh  # start at 50 % SoC

    for ts in timestamps:
        hour = ts.hour + ts.minute / 60.0
        is_weekend = ts.weekday() >= 5

        # Cloud cover varies slowly over the day
        cloud_factor = float(np.clip(1.0 - rng.normal(CLOUD_MEAN, CLOUD_STD), MIN_CLOUD_FACTOR, MAX_CLOUD_FACTOR))
        irradiance = _solar_irradiance(hour, cloud_factor)
        temperature_c = 20 + 10 * np.sin(np.pi * (hour - 6) / 12) + rng.normal(0, 1.5)

        solar_gen_kw = solar_capacity_kw * irradiance + rng.normal(0, 2)
        solar_gen_kw = float(np.clip(solar_gen_kw, 0, solar_capacity_kw))

        demand_kw = _campus_load_kw(hour, is_weekend) + rng.normal(0, 15)
        demand_kw = float(np.clip(demand_kw, 50, 700))

        # Simple battery simulation: charge when solar > demand, discharge otherwise
        net_power = solar_gen_kw - demand_kw  # positive → surplus
        dt_h = interval_minutes / 60.0
        charge_efficiency = 0.95
        discharge_efficiency = 0.95

        if net_power > 0:
            charge_kw = min(net_power, (battery_capacity_kwh - battery_soc) / dt_h)
            battery_soc += charge_kw * dt_h * charge_efficiency
            grid_import_kw = 0.0
            grid_export_kw = net_power - charge_kw
        else:
            discharge_kw = min(-net_power, battery_soc / dt_h * discharge_efficiency)
            battery_soc -= discharge_kw / discharge_efficiency * dt_h
            grid_import_kw = max(0.0, -net_power - discharge_kw)
            grid_export_kw = 0.0

        battery_soc = float(np.clip(battery_soc, 0, battery_capacity_kwh))
        battery_soc_pct = battery_soc / battery_capacity_kwh * 100.0

        # Inject random anomalies (~1 % of samples)
        is_anomaly = bool(rng.random() < 0.01)
        if is_anomaly:
            demand_kw *= rng.uniform(1.5, 2.5)

        records.append(
            {
                "timestamp": ts,
                "hour": hour,
                "day_of_week": ts.weekday(),
                "month": ts.month,
                "is_weekend": int(is_weekend),
                "temperature_c": round(float(temperature_c), 2),
                "irradiance_norm": round(irradiance, 4),
                "cloud_factor": round(cloud_factor, 4),
                "solar_gen_kw": round(solar_gen_kw, 2),
                "demand_kw": round(demand_kw, 2),
                "battery_soc_kwh": round(battery_soc, 2),
                "battery_soc_pct": round(battery_soc_pct, 2),
                "grid_import_kw": round(float(np.clip(grid_import_kw, 0, None)), 2),
                "grid_export_kw": round(float(np.clip(grid_export_kw, 0, None)), 2),
                "is_anomaly": int(is_anomaly),
            }
        )

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_live_reading(
    solar_capacity_kw: float = 300.0,
    battery_soc_pct: float = 60.0,
    random_seed: int | None = None,
) -> dict:
    """
    Return a single simulated 'live' sensor reading for the current moment.

    Parameters
    ----------
    solar_capacity_kw : float
        Installed peak solar capacity in kW.
    battery_soc_pct : float
        Current battery state of charge (%).
    random_seed : int or None
        Optional seed for reproducibility in tests.

    Returns
    -------
    dict
        Dictionary of sensor values.
    """
    rng = np.random.default_rng(random_seed)
    now = datetime.now()
    hour = now.hour + now.minute / 60.0
    is_weekend = now.weekday() >= 5

    cloud_factor = float(np.clip(1.0 - rng.normal(CLOUD_MEAN, CLOUD_STD), MIN_CLOUD_FACTOR, MAX_CLOUD_FACTOR))
    irradiance = _solar_irradiance(hour, cloud_factor)
    temperature_c = 20 + 10 * np.sin(np.pi * (hour - 6) / 12) + rng.normal(0, 1.5)
    solar_gen_kw = float(np.clip(solar_capacity_kw * irradiance + rng.normal(0, 2), 0, solar_capacity_kw))
    demand_kw = float(np.clip(_campus_load_kw(hour, is_weekend) + rng.normal(0, 15), 50, 700))

    return {
        "timestamp": now.isoformat(),
        "temperature_c": round(float(temperature_c), 2),
        "irradiance_norm": round(irradiance, 4),
        "solar_gen_kw": round(solar_gen_kw, 2),
        "demand_kw": round(demand_kw, 2),
        "battery_soc_pct": round(battery_soc_pct, 2),
        "grid_import_kw": round(max(0.0, demand_kw - solar_gen_kw), 2),
        "grid_export_kw": round(max(0.0, solar_gen_kw - demand_kw), 2),
    }
