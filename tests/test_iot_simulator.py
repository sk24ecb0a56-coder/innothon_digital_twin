"""Unit tests for the IoT data simulator."""

import pytest
import pandas as pd
import numpy as np

from src.data.iot_simulator import generate_iot_data, get_live_reading, _solar_irradiance


class TestSolarIrradiance:
    def test_zero_at_night(self):
        assert _solar_irradiance(2.0) == 0.0
        assert _solar_irradiance(22.0) == 0.0

    def test_positive_during_day(self):
        assert _solar_irradiance(12.0) > 0.0

    def test_cloud_factor_reduces_output(self):
        full_sun = _solar_irradiance(12.0, cloud_factor=1.0)
        cloudy = _solar_irradiance(12.0, cloud_factor=0.3)
        assert cloudy < full_sun

    def test_boundary_hours(self):
        assert _solar_irradiance(6.0) == pytest.approx(0.0, abs=1e-6)
        assert _solar_irradiance(20.0) == pytest.approx(0.0, abs=1e-6)


class TestGenerateIoTData:
    def setup_method(self):
        self.df = generate_iot_data(days=3, interval_minutes=15, random_seed=42)

    def test_returns_dataframe(self):
        assert isinstance(self.df, pd.DataFrame)

    def test_expected_row_count(self):
        expected = 3 * 24 * 4  # 3 days × 96 intervals/day
        assert len(self.df) == expected

    def test_required_columns_present(self):
        required = [
            "timestamp", "hour", "day_of_week", "month", "is_weekend",
            "temperature_c", "irradiance_norm", "solar_gen_kw", "demand_kw",
            "battery_soc_kwh", "battery_soc_pct", "grid_import_kw",
            "grid_export_kw", "is_anomaly",
        ]
        for col in required:
            assert col in self.df.columns, f"Missing column: {col}"

    def test_solar_non_negative(self):
        assert (self.df["solar_gen_kw"] >= 0).all()

    def test_demand_positive(self):
        assert (self.df["demand_kw"] > 0).all()

    def test_battery_soc_within_bounds(self):
        assert (self.df["battery_soc_pct"] >= 0).all()
        assert (self.df["battery_soc_pct"] <= 100).all()

    def test_timestamps_monotonically_increasing(self):
        assert self.df["timestamp"].is_monotonic_increasing

    def test_reproducibility(self):
        df2 = generate_iot_data(days=3, interval_minutes=15, random_seed=42)
        pd.testing.assert_frame_equal(self.df, df2)

    def test_anomaly_flag_binary(self):
        assert set(self.df["is_anomaly"].unique()).issubset({0, 1})


class TestGetLiveReading:
    def test_returns_dict(self):
        reading = get_live_reading(random_seed=0)
        assert isinstance(reading, dict)

    def test_required_keys(self):
        reading = get_live_reading(random_seed=0)
        for key in ["timestamp", "solar_gen_kw", "demand_kw", "battery_soc_pct"]:
            assert key in reading

    def test_solar_non_negative(self):
        reading = get_live_reading(random_seed=0)
        assert reading["solar_gen_kw"] >= 0

    def test_demand_positive(self):
        reading = get_live_reading(random_seed=0)
        assert reading["demand_kw"] > 0
