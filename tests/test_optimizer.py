"""Unit tests for the solar & battery optimizer."""

import pytest
import pandas as pd
import numpy as np

from src.data.iot_simulator import generate_iot_data
from src.optimization.solar_battery_optimizer import (
    SolarBatteryOptimizer,
    SystemConfig,
    BatteryAction,
    OptimizationResult,
)

SOC_TOLERANCE_KWH = 1.0  # Allowed floating-point tolerance on SoC bounds (kWh)


@pytest.fixture
def config():
    return SystemConfig(
        solar_capacity_kw=300.0,
        battery_capacity_kwh=500.0,
        battery_max_charge_kw=100.0,
        battery_max_discharge_kw=100.0,
        soc_min_pct=10.0,
        soc_max_pct=95.0,
    )


@pytest.fixture
def optimizer(config):
    return SolarBatteryOptimizer(config=config)


@pytest.fixture(scope="module")
def sim_result():
    df = generate_iot_data(days=7, random_seed=42)
    opt = SolarBatteryOptimizer()
    return opt, opt.run_simulation(df), df


class TestOptimizerStep:
    def test_returns_result_object(self, optimizer):
        result = optimizer.step(solar_gen_kw=200.0, demand_kw=150.0, battery_soc_kwh=250.0, hour=12.0)
        assert isinstance(result, OptimizationResult)

    def test_surplus_solar_charges_battery(self, optimizer):
        result = optimizer.step(solar_gen_kw=300.0, demand_kw=100.0, battery_soc_kwh=250.0, hour=12.0)
        assert result.battery_action == BatteryAction.CHARGE
        assert result.battery_power_kw > 0

    def test_deficit_discharges_battery(self, optimizer):
        result = optimizer.step(solar_gen_kw=50.0, demand_kw=300.0, battery_soc_kwh=400.0, hour=14.0)
        assert result.battery_action == BatteryAction.DISCHARGE
        assert result.battery_power_kw < 0

    def test_full_battery_prevents_overcharge(self, optimizer, config):
        full_soc = config.battery_capacity_kwh * config.soc_max_pct / 100
        result = optimizer.step(solar_gen_kw=300.0, demand_kw=100.0, battery_soc_kwh=full_soc, hour=12.0)
        assert result.battery_soc_kwh <= full_soc + SOC_TOLERANCE_KWH

    def test_empty_battery_prevents_overdischarge(self, optimizer, config):
        min_soc = config.battery_capacity_kwh * config.soc_min_pct / 100
        result = optimizer.step(solar_gen_kw=0.0, demand_kw=300.0, battery_soc_kwh=min_soc, hour=14.0)
        assert result.battery_soc_kwh >= min_soc - SOC_TOLERANCE_KWH

    def test_soc_bounded(self, optimizer, config):
        result = optimizer.step(solar_gen_kw=200.0, demand_kw=150.0, battery_soc_kwh=250.0, hour=10.0)
        assert config.soc_min_pct / 100 * config.battery_capacity_kwh - SOC_TOLERANCE_KWH <= result.battery_soc_kwh
        assert result.battery_soc_kwh <= config.soc_max_pct / 100 * config.battery_capacity_kwh + SOC_TOLERANCE_KWH

    def test_non_negative_grid_values(self, optimizer):
        result = optimizer.step(solar_gen_kw=100.0, demand_kw=200.0, battery_soc_kwh=100.0, hour=15.0)
        assert result.grid_import_kw >= 0.0
        assert result.grid_export_kw >= 0.0

    def test_recommendation_is_string(self, optimizer):
        result = optimizer.step(solar_gen_kw=200.0, demand_kw=150.0, battery_soc_kwh=250.0, hour=12.0)
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0


class TestOptimizerSimulation:
    def test_run_simulation_returns_dataframe(self, sim_result):
        opt, df, _ = sim_result
        assert isinstance(df, pd.DataFrame)

    def test_simulation_columns_added(self, sim_result):
        _, df, _ = sim_result
        for col in [
            "opt_battery_action", "opt_battery_power_kw", "opt_grid_import_kw",
            "opt_grid_export_kw", "opt_battery_soc_kwh", "opt_battery_soc_pct",
            "opt_energy_cost_inr", "opt_cost_savings_inr",
        ]:
            assert col in df.columns, f"Missing column: {col}"

    def test_soc_within_bounds_throughout(self, sim_result, config):
        _, df, _ = sim_result
        opt = SolarBatteryOptimizer()
        cfg = opt.config
        assert (df["opt_battery_soc_pct"] >= cfg.soc_min_pct - SOC_TOLERANCE_KWH).all()
        assert (df["opt_battery_soc_pct"] <= cfg.soc_max_pct + SOC_TOLERANCE_KWH).all()

    def test_grid_import_non_negative(self, sim_result):
        _, df, _ = sim_result
        assert (df["opt_grid_import_kw"] >= 0).all()

    def test_grid_export_non_negative(self, sim_result):
        _, df, _ = sim_result
        assert (df["opt_grid_export_kw"] >= 0).all()


class TestOptimizerKPIs:
    def test_get_kpis_returns_dict(self, sim_result):
        opt, df, _ = sim_result
        kpis = opt.get_kpis(df)
        assert isinstance(kpis, dict)

    def test_self_sufficiency_in_range(self, sim_result):
        opt, df, _ = sim_result
        kpis = opt.get_kpis(df)
        assert 0 <= kpis["self_sufficiency_pct"] <= 100

    def test_solar_fraction_positive(self, sim_result):
        opt, df, _ = sim_result
        kpis = opt.get_kpis(df)
        assert kpis["solar_fraction_pct"] >= 0

    def test_required_kpi_keys(self, sim_result):
        opt, df, _ = sim_result
        kpis = opt.get_kpis(df)
        for key in [
            "total_demand_kwh", "total_solar_kwh", "total_grid_import_kwh",
            "total_grid_export_kwh", "self_sufficiency_pct", "solar_fraction_pct",
            "total_cost_savings_inr", "avg_battery_soc_pct",
        ]:
            assert key in kpis, f"Missing KPI: {key}"
