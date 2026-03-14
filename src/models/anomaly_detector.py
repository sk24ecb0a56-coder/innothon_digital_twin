"""
Anomaly Detector for Campus Energy Systems.

Uses an Isolation Forest to identify abnormal energy usage patterns and
potential equipment faults based on IoT sensor readings.
"""

from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


ANOMALY_FEATURES = [
    "hour",
    "is_weekend",
    "temperature_c",
    "demand_kw",
    "solar_gen_kw",
    "battery_soc_pct",
    "grid_import_kw",
]

FAULT_RULES = {
    "demand_spike": {"threshold_multiplier": 1.8, "description": "Demand spike (>1.8× rolling mean)"},
    "solar_underperform": {"threshold_fraction": 0.3, "description": "Solar underperformance (<30 % expected at peak irradiance)"},
    "battery_low": {"threshold_pct": 10.0, "description": "Battery critically low (<10 % SoC)"},
    "battery_high": {"threshold_pct": 95.0, "description": "Battery near full (>95 % SoC, risk of overcharge)"},
    "grid_overload": {"threshold_kw": 200.0, "description": "High grid import (>200 kW)"},
}


class AnomalyDetector:
    """
    Detects anomalies and potential equipment faults in campus energy data.

    Combines:
    - A statistical Isolation Forest for ML-based anomaly scoring.
    - Rule-based fault detection for interpretable alerts.

    Parameters
    ----------
    contamination : float
        Expected fraction of anomalies in training data (for Isolation Forest).
    random_state : int
        Seed for reproducibility.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        solar_capacity_kw: float = 300.0,
    ) -> None:
        self.contamination = contamination
        self.random_state = random_state
        self.solar_capacity_kw = solar_capacity_kw
        self._model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            n_jobs=-1,
        )
        self._scaler = StandardScaler()
        self.is_fitted = False
        self.threshold_: float = 0.0

    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        """
        Train the Isolation Forest on historical IoT data.

        Parameters
        ----------
        df : pd.DataFrame
            Historical data returned by ``generate_iot_data``.

        Returns
        -------
        AnomalyDetector
            The fitted instance.
        """
        X = df[ANOMALY_FEATURES].values
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled)
        scores = self._model.score_samples(X_scaled)
        # Keep the threshold at the 5th percentile of normal-sample scores
        normal_mask = df["is_anomaly"] == 0 if "is_anomaly" in df.columns else np.ones(len(df), dtype=bool)
        self.threshold_ = float(np.percentile(scores[normal_mask], 5))
        self.is_fitted = True
        return self

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Return anomaly scores for each row (lower = more anomalous).

        Parameters
        ----------
        df : pd.DataFrame
            Sensor readings with at least the columns in ``ANOMALY_FEATURES``.

        Returns
        -------
        np.ndarray
            Array of raw anomaly scores from Isolation Forest.
        """
        self._check_fitted()
        X = df[ANOMALY_FEATURES].values
        X_scaled = self._scaler.transform(X)
        return self._model.score_samples(X_scaled)

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Label each row as anomalous (1) or normal (0) and apply fault rules.

        Parameters
        ----------
        df : pd.DataFrame
            Sensor readings.

        Returns
        -------
        pd.DataFrame
            Original DataFrame with additional columns:
            - ``anomaly_score``
            - ``is_ml_anomaly`` (from Isolation Forest)
            - ``fault_flags`` (comma-separated rule-based faults)
            - ``is_anomaly_any`` (1 if either ML or rule-based anomaly)
        """
        self._check_fitted()
        result = df.copy()
        scores = self.score(df)
        result["anomaly_score"] = scores
        result["is_ml_anomaly"] = (scores < self.threshold_).astype(int)
        result["fault_flags"] = self._apply_rules(df)
        result["is_anomaly_any"] = (
            (result["is_ml_anomaly"] == 1) | (result["fault_flags"] != "")
        ).astype(int)
        return result

    def predict_single(self, reading: dict) -> dict:
        """
        Evaluate a single sensor reading for anomalies.

        Parameters
        ----------
        reading : dict
            Key-value sensor reading. Must contain all ``ANOMALY_FEATURES``.

        Returns
        -------
        dict
            Enriched reading with anomaly_score, is_ml_anomaly, fault_flags.
        """
        self._check_fitted()
        row_df = pd.DataFrame([reading])
        result_df = self.predict(row_df)
        row = result_df.iloc[0]
        return {
            **reading,
            "anomaly_score": float(row["anomaly_score"]),
            "is_ml_anomaly": int(row["is_ml_anomaly"]),
            "fault_flags": row["fault_flags"],
            "is_anomaly_any": int(row["is_anomaly_any"]),
        }

    def save(self, directory: str) -> None:
        """Persist model and scaler to ``directory``."""
        os.makedirs(directory, exist_ok=True)
        joblib.dump(self._model, os.path.join(directory, "anomaly_model.pkl"))
        joblib.dump(self._scaler, os.path.join(directory, "anomaly_scaler.pkl"))
        joblib.dump(
            {"threshold": self.threshold_, "solar_capacity_kw": self.solar_capacity_kw},
            os.path.join(directory, "anomaly_meta.pkl"),
        )

    @classmethod
    def load(cls, directory: str) -> "AnomalyDetector":
        """Load a previously saved ``AnomalyDetector`` from ``directory``."""
        detector = cls()
        detector._model = joblib.load(os.path.join(directory, "anomaly_model.pkl"))
        detector._scaler = joblib.load(os.path.join(directory, "anomaly_scaler.pkl"))
        meta = joblib.load(os.path.join(directory, "anomaly_meta.pkl"))
        detector.threshold_ = meta["threshold"]
        detector.solar_capacity_kw = meta.get("solar_capacity_kw", 300.0)
        detector.is_fitted = True
        return detector

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_fitted(self) -> None:
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetector must be fitted before calling predict.")

    def _apply_rules(self, df: pd.DataFrame) -> pd.Series:
        """Apply deterministic rule-based fault checks."""
        flags = pd.Series([""] * len(df), index=df.index)

        # Demand spike: > 1.8× 4-interval rolling mean
        if "demand_kw" in df.columns:
            rolling = df["demand_kw"].rolling(window=4, min_periods=1).mean().shift(1)
            rolling = rolling.fillna(df["demand_kw"].iloc[0])
            spike_mask = df["demand_kw"] > FAULT_RULES["demand_spike"]["threshold_multiplier"] * rolling
            flags[spike_mask] = _append_flag(flags[spike_mask], "demand_spike")

        # Solar underperformance at peak hours (uses configured solar capacity)
        if "solar_gen_kw" in df.columns and "irradiance_norm" in df.columns:
            expected_frac = df["irradiance_norm"] * self.solar_capacity_kw
            underperform = (
                (df["irradiance_norm"] > 0.5)
                & (df["solar_gen_kw"] < FAULT_RULES["solar_underperform"]["threshold_fraction"] * expected_frac)
            )
            flags[underperform] = _append_flag(flags[underperform], "solar_underperform")

        # Battery critical low
        if "battery_soc_pct" in df.columns:
            low_mask = df["battery_soc_pct"] < FAULT_RULES["battery_low"]["threshold_pct"]
            flags[low_mask] = _append_flag(flags[low_mask], "battery_low")

            high_mask = df["battery_soc_pct"] > FAULT_RULES["battery_high"]["threshold_pct"]
            flags[high_mask] = _append_flag(flags[high_mask], "battery_high")

        # Grid overload
        if "grid_import_kw" in df.columns:
            overload_mask = df["grid_import_kw"] > FAULT_RULES["grid_overload"]["threshold_kw"]
            flags[overload_mask] = _append_flag(flags[overload_mask], "grid_overload")

        return flags


def _append_flag(series: pd.Series, flag: str) -> pd.Series:
    """Append a fault flag string, comma-separated if multiple."""
    return series.apply(lambda s: f"{s},{flag}" if s else flag)
