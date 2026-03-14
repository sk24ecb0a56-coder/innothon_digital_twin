"""
Energy Demand and Solar Generation Predictor.

Uses Random Forest regressors trained on historical IoT data to predict:
- Campus energy demand (kW) for the next interval
- Solar power generation (kW) for the next interval
"""

from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler


DEMAND_FEATURES = [
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "temperature_c",
    "demand_kw_lag1",
    "demand_kw_lag4",
    "demand_kw_rolling_mean",
]

SOLAR_FEATURES = [
    "hour",
    "month",
    "temperature_c",
    "irradiance_norm",
    "cloud_factor",
    "solar_gen_kw_lag1",
]


def _add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return df enriched with lag and rolling features."""
    df = df.copy()
    df["demand_kw_lag1"] = df["demand_kw"].shift(1)
    df["demand_kw_lag4"] = df["demand_kw"].shift(4)
    df["demand_kw_rolling_mean"] = df["demand_kw"].shift(1).rolling(window=4).mean()
    df["solar_gen_kw_lag1"] = df["solar_gen_kw"].shift(1)
    df = df.dropna()
    return df


class EnergyPredictor:
    """
    Trains and serves ML predictions for campus energy demand and solar generation.

    Parameters
    ----------
    n_estimators : int
        Number of trees in each Random Forest.
    random_state : int
        Seed for reproducibility.
    """

    def __init__(self, n_estimators: int = 100, random_state: int = 42) -> None:
        self.n_estimators = n_estimators
        self.random_state = random_state

        self._demand_model = RandomForestRegressor(
            n_estimators=n_estimators, random_state=random_state, n_jobs=-1
        )
        self._solar_model = RandomForestRegressor(
            n_estimators=n_estimators, random_state=random_state, n_jobs=-1
        )
        self._demand_scaler = StandardScaler()
        self._solar_scaler = StandardScaler()
        self.is_fitted = False
        self.metrics: dict[str, float] = {}

    def fit(self, df: pd.DataFrame, test_size: float = 0.2) -> "EnergyPredictor":
        """
        Train both models on historical IoT data.

        Parameters
        ----------
        df : pd.DataFrame
            Historical data returned by ``generate_iot_data``.
        test_size : float
            Fraction of data to hold out for evaluation.

        Returns
        -------
        EnergyPredictor
            The fitted instance (for chaining).
        """
        df = _add_lag_features(df)

        # --- Demand model ---
        X_d = df[DEMAND_FEATURES].values
        y_d = df["demand_kw"].values
        X_d_train, X_d_test, y_d_train, y_d_test = train_test_split(
            X_d, y_d, test_size=test_size, shuffle=False
        )
        X_d_train = self._demand_scaler.fit_transform(X_d_train)
        X_d_test = self._demand_scaler.transform(X_d_test)
        self._demand_model.fit(X_d_train, y_d_train)
        d_preds = self._demand_model.predict(X_d_test)
        self.metrics["demand_mae"] = float(mean_absolute_error(y_d_test, d_preds))
        self.metrics["demand_r2"] = float(r2_score(y_d_test, d_preds))

        # --- Solar model ---
        X_s = df[SOLAR_FEATURES].values
        y_s = df["solar_gen_kw"].values
        X_s_train, X_s_test, y_s_train, y_s_test = train_test_split(
            X_s, y_s, test_size=test_size, shuffle=False
        )
        X_s_train = self._solar_scaler.fit_transform(X_s_train)
        X_s_test = self._solar_scaler.transform(X_s_test)
        self._solar_model.fit(X_s_train, y_s_train)
        s_preds = self._solar_model.predict(X_s_test)
        self.metrics["solar_mae"] = float(mean_absolute_error(y_s_test, s_preds))
        self.metrics["solar_r2"] = float(r2_score(y_s_test, s_preds))

        self.is_fitted = True
        return self

    def predict_demand(self, features: dict | pd.DataFrame) -> float:
        """
        Predict energy demand (kW) for a single interval.

        Parameters
        ----------
        features : dict or pd.DataFrame
            Must contain all keys in ``DEMAND_FEATURES``.

        Returns
        -------
        float
            Predicted demand in kW (clipped to >= 0).
        """
        self._check_fitted()
        row = self._to_row(features, DEMAND_FEATURES)
        scaled = self._demand_scaler.transform(row)
        pred = self._demand_model.predict(scaled)[0]
        return float(np.clip(pred, 0, None))

    def predict_solar(self, features: dict | pd.DataFrame) -> float:
        """
        Predict solar generation (kW) for a single interval.

        Parameters
        ----------
        features : dict or pd.DataFrame
            Must contain all keys in ``SOLAR_FEATURES``.

        Returns
        -------
        float
            Predicted solar generation in kW (clipped to >= 0).
        """
        self._check_fitted()
        row = self._to_row(features, SOLAR_FEATURES)
        scaled = self._solar_scaler.transform(row)
        pred = self._solar_model.predict(scaled)[0]
        return float(np.clip(pred, 0, None))

    def predict_horizon(
        self, current_row: pd.Series, horizon_steps: int = 4
    ) -> pd.DataFrame:
        """
        Predict demand and solar generation for the next ``horizon_steps`` intervals.

        Parameters
        ----------
        current_row : pd.Series
            Latest sensor reading (must have all feature columns).
        horizon_steps : int
            Number of 15-minute intervals to forecast.

        Returns
        -------
        pd.DataFrame
            Columns: step, predicted_demand_kw, predicted_solar_kw.
        """
        self._check_fitted()
        results = []
        prev_demand = current_row.get("demand_kw", 300.0)
        prev_solar = current_row.get("solar_gen_kw", 0.0)

        # Build a mutable feature dict from the current row
        row = current_row.to_dict() if hasattr(current_row, "to_dict") else dict(current_row)

        for step in range(1, horizon_steps + 1):
            # Advance hour by one interval (15 min)
            row["hour"] = (row.get("hour", 12.0) + 0.25) % 24

            # Update lag features
            row["demand_kw_lag1"] = prev_demand
            row["demand_kw_lag4"] = prev_demand  # simplified
            row["demand_kw_rolling_mean"] = prev_demand
            row["solar_gen_kw_lag1"] = prev_solar

            pred_d = self.predict_demand(row)
            pred_s = self.predict_solar(row)

            results.append(
                {
                    "step": step,
                    "predicted_demand_kw": round(pred_d, 2),
                    "predicted_solar_kw": round(pred_s, 2),
                }
            )
            prev_demand = pred_d
            prev_solar = pred_s

        return pd.DataFrame(results)

    def save(self, directory: str) -> None:
        """Persist models and scalers to ``directory``."""
        os.makedirs(directory, exist_ok=True)
        joblib.dump(self._demand_model, os.path.join(directory, "demand_model.pkl"))
        joblib.dump(self._solar_model, os.path.join(directory, "solar_model.pkl"))
        joblib.dump(self._demand_scaler, os.path.join(directory, "demand_scaler.pkl"))
        joblib.dump(self._solar_scaler, os.path.join(directory, "solar_scaler.pkl"))

    @classmethod
    def load(cls, directory: str) -> "EnergyPredictor":
        """Load a previously saved ``EnergyPredictor`` from ``directory``."""
        predictor = cls()
        predictor._demand_model = joblib.load(os.path.join(directory, "demand_model.pkl"))
        predictor._solar_model = joblib.load(os.path.join(directory, "solar_model.pkl"))
        predictor._demand_scaler = joblib.load(os.path.join(directory, "demand_scaler.pkl"))
        predictor._solar_scaler = joblib.load(os.path.join(directory, "solar_scaler.pkl"))
        predictor.is_fitted = True
        return predictor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_fitted(self) -> None:
        if not self.is_fitted:
            raise RuntimeError("EnergyPredictor must be fitted before calling predict.")

    @staticmethod
    def _to_row(features: dict | pd.DataFrame, columns: list[str]) -> np.ndarray:
        if isinstance(features, pd.DataFrame):
            return features[columns].values[:1]
        return np.array([[features[c] for c in columns]])
