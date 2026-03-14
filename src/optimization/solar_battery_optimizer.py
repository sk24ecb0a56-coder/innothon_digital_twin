"""
Solar and Battery Storage Optimizer.

Provides intelligent dispatch decisions for campus energy systems by
optimizing when to:
- Charge the battery (solar surplus or cheap grid tariff)
- Discharge the battery (peak demand, high grid price)
- Export surplus solar to the grid
- Import from the grid (last resort)

Implements a rule-based greedy optimizer with optional look-ahead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd


class BatteryAction(str, Enum):
    CHARGE = "charge"
    DISCHARGE = "discharge"
    IDLE = "idle"


@dataclass
class SystemConfig:
    """Physical and economic parameters of the campus energy system."""

    solar_capacity_kw: float = 300.0
    battery_capacity_kwh: float = 500.0
    battery_max_charge_kw: float = 100.0
    battery_max_discharge_kw: float = 100.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    soc_min_pct: float = 10.0
    soc_max_pct: float = 95.0
    grid_import_cost_per_kwh: float = 8.0   # INR / kWh
    grid_export_price_per_kwh: float = 3.0  # INR / kWh (feed-in tariff)
    peak_hours: tuple[int, int] = (9, 18)   # hours with peak demand tariff
    peak_tariff_multiplier: float = 1.5
    offpeak_discharge_factor: float = 0.8   # Conservative discharge fraction during off-peak (reduces battery wear)


@dataclass
class OptimizationResult:
    """Result of a single optimization step."""

    battery_action: BatteryAction
    battery_power_kw: float           # Positive = charging, Negative = discharging
    grid_import_kw: float
    grid_export_kw: float
    battery_soc_kwh: float
    battery_soc_pct: float
    energy_cost_inr: float
    cost_savings_inr: float
    recommendation: str
    metrics: dict = field(default_factory=dict)


class SolarBatteryOptimizer:
    """
    Greedy rule-based optimizer for solar + battery dispatch.

    The optimizer follows a priority stack:
    1. Serve campus load from solar generation (zero cost).
    2. If solar > load, charge battery up to ``soc_max_pct``.
    3. If battery still not full, export excess solar to grid.
    4. If solar < load, discharge battery to serve the deficit.
    5. Any remaining deficit is imported from the grid.

    During peak hours, battery discharge is prioritised more aggressively
    to minimise expensive grid imports.

    Parameters
    ----------
    config : SystemConfig
        Physical and tariff parameters.
    """

    def __init__(self, config: SystemConfig | None = None) -> None:
        self.config = config or SystemConfig()

    def step(
        self,
        solar_gen_kw: float,
        demand_kw: float,
        battery_soc_kwh: float,
        hour: float,
        dt_h: float = 0.25,
    ) -> OptimizationResult:
        """
        Compute the optimal dispatch for a single time interval.

        Parameters
        ----------
        solar_gen_kw : float
            Current solar generation (kW).
        demand_kw : float
            Current campus demand (kW).
        battery_soc_kwh : float
            Current battery state of charge (kWh).
        hour : float
            Current hour of day (0–24).
        dt_h : float
            Interval duration in hours (default 0.25 = 15 min).

        Returns
        -------
        OptimizationResult
            Dispatch decision and economic metrics.
        """
        cfg = self.config
        is_peak = cfg.peak_hours[0] <= int(hour) < cfg.peak_hours[1]
        tariff = cfg.grid_import_cost_per_kwh * (cfg.peak_tariff_multiplier if is_peak else 1.0)

        soc_min_kwh = cfg.soc_min_pct / 100 * cfg.battery_capacity_kwh
        soc_max_kwh = cfg.soc_max_pct / 100 * cfg.battery_capacity_kwh

        net = solar_gen_kw - demand_kw  # positive → surplus

        battery_power_kw = 0.0  # + = charging
        grid_import_kw = 0.0
        grid_export_kw = 0.0
        new_soc_kwh = battery_soc_kwh

        if net >= 0:
            # Surplus solar
            chargeable = (soc_max_kwh - battery_soc_kwh) / (dt_h * cfg.charge_efficiency + 1e-9)
            chargeable = min(chargeable, cfg.battery_max_charge_kw)
            charge_kw = min(net, chargeable)
            new_soc_kwh = battery_soc_kwh + charge_kw * dt_h * cfg.charge_efficiency
            battery_power_kw = charge_kw
            grid_export_kw = max(0.0, net - charge_kw)
            action = BatteryAction.CHARGE if charge_kw > 0.01 else BatteryAction.IDLE
        else:
            # Deficit: discharge battery
            deficit = -net
            dischargeable = (battery_soc_kwh - soc_min_kwh) * cfg.discharge_efficiency / dt_h
            dischargeable = min(dischargeable, cfg.battery_max_discharge_kw)

            # During peak hours, be more aggressive in discharging
            if is_peak:
                discharge_kw = min(deficit, dischargeable)
            else:
                discharge_kw = min(deficit * cfg.offpeak_discharge_factor, dischargeable)

            new_soc_kwh = battery_soc_kwh - discharge_kw / cfg.discharge_efficiency * dt_h
            battery_power_kw = -discharge_kw
            grid_import_kw = max(0.0, deficit - discharge_kw)
            action = BatteryAction.DISCHARGE if discharge_kw > 0.01 else BatteryAction.IDLE

        new_soc_kwh = float(np.clip(new_soc_kwh, soc_min_kwh, soc_max_kwh))
        soc_pct = new_soc_kwh / cfg.battery_capacity_kwh * 100.0

        energy_cost = grid_import_kw * dt_h * tariff
        savings = grid_export_kw * dt_h * cfg.grid_export_price_per_kwh

        # Baseline cost: if no battery, all deficit from grid
        baseline_import = max(0.0, demand_kw - solar_gen_kw)
        baseline_cost = baseline_import * dt_h * tariff
        cost_savings = baseline_cost - energy_cost + savings

        recommendation = self._recommend(action, solar_gen_kw, demand_kw, soc_pct, is_peak)

        return OptimizationResult(
            battery_action=action,
            battery_power_kw=round(battery_power_kw, 2),
            grid_import_kw=round(grid_import_kw, 2),
            grid_export_kw=round(grid_export_kw, 2),
            battery_soc_kwh=round(new_soc_kwh, 2),
            battery_soc_pct=round(soc_pct, 2),
            energy_cost_inr=round(energy_cost, 2),
            cost_savings_inr=round(cost_savings, 2),
            recommendation=recommendation,
            metrics={
                "tariff_inr_kwh": tariff,
                "is_peak_hour": is_peak,
                "solar_coverage_pct": round(min(solar_gen_kw / max(demand_kw, 1) * 100, 100), 1),
            },
        )

    def run_simulation(
        self,
        df: pd.DataFrame,
        initial_soc_kwh: float | None = None,
    ) -> pd.DataFrame:
        """
        Run the optimizer over a historical/simulated dataset.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with columns: solar_gen_kw, demand_kw, hour.
        initial_soc_kwh : float or None
            Starting battery SoC. Defaults to 50 % of capacity.

        Returns
        -------
        pd.DataFrame
            Original DataFrame with additional optimiser output columns.
        """
        if initial_soc_kwh is None:
            initial_soc_kwh = 0.5 * self.config.battery_capacity_kwh

        records = []
        soc = initial_soc_kwh

        for _, row in df.iterrows():
            result = self.step(
                solar_gen_kw=row["solar_gen_kw"],
                demand_kw=row["demand_kw"],
                battery_soc_kwh=soc,
                hour=row["hour"],
            )
            soc = result.battery_soc_kwh
            records.append(
                {
                    "opt_battery_action": result.battery_action.value,
                    "opt_battery_power_kw": result.battery_power_kw,
                    "opt_grid_import_kw": result.grid_import_kw,
                    "opt_grid_export_kw": result.grid_export_kw,
                    "opt_battery_soc_kwh": result.battery_soc_kwh,
                    "opt_battery_soc_pct": result.battery_soc_pct,
                    "opt_energy_cost_inr": result.energy_cost_inr,
                    "opt_cost_savings_inr": result.cost_savings_inr,
                    "opt_recommendation": result.recommendation,
                    "opt_solar_coverage_pct": result.metrics["solar_coverage_pct"],
                }
            )

        opt_df = pd.DataFrame(records, index=df.index)
        return pd.concat([df, opt_df], axis=1)

    def get_kpis(self, sim_df: pd.DataFrame) -> dict:
        """
        Compute summary KPIs from an optimizer simulation run.

        Parameters
        ----------
        sim_df : pd.DataFrame
            Output from ``run_simulation``.

        Returns
        -------
        dict
            Dictionary of key performance indicators.
        """
        dt_h = 0.25
        total_demand_kwh = sim_df["demand_kw"].sum() * dt_h
        total_solar_kwh = sim_df["solar_gen_kw"].sum() * dt_h
        total_grid_import_kwh = sim_df["opt_grid_import_kw"].sum() * dt_h
        total_grid_export_kwh = sim_df["opt_grid_export_kw"].sum() * dt_h
        total_cost_savings = sim_df["opt_cost_savings_inr"].sum()
        self_sufficiency = (total_demand_kwh - total_grid_import_kwh) / max(total_demand_kwh, 1) * 100

        return {
            "total_demand_kwh": round(total_demand_kwh, 1),
            "total_solar_kwh": round(total_solar_kwh, 1),
            "total_grid_import_kwh": round(total_grid_import_kwh, 1),
            "total_grid_export_kwh": round(total_grid_export_kwh, 1),
            "self_sufficiency_pct": round(self_sufficiency, 1),
            "solar_fraction_pct": round(total_solar_kwh / max(total_demand_kwh, 1) * 100, 1),
            "total_cost_savings_inr": round(total_cost_savings, 2),
            "avg_battery_soc_pct": round(sim_df["opt_battery_soc_pct"].mean(), 1),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _recommend(
        action: BatteryAction,
        solar_kw: float,
        demand_kw: float,
        soc_pct: float,
        is_peak: bool,
    ) -> str:
        if action == BatteryAction.CHARGE:
            return f"Charging battery from solar surplus ({solar_kw - demand_kw:.0f} kW excess)."
        elif action == BatteryAction.DISCHARGE:
            suffix = " (peak tariff active)" if is_peak else ""
            return f"Discharging battery to reduce grid import{suffix}. SoC: {soc_pct:.1f} %."
        else:
            if solar_kw >= demand_kw:
                return "Solar fully covering load. Battery idle."
            elif soc_pct <= 15:
                return "Battery near empty. Importing from grid."
            else:
                return "Balanced operation. No battery action needed."
