"""Unit tests for the energy predictor ML models."""

import pytest
import pandas as pd
import numpy as np

from src.data.iot_simulator import generate_iot_data
from src.models.energy_predictor import EnergyPredictor, DEMAND_FEATURES, SOLAR_FEATURES


@pytest.fixture(scope="module")
def fitted_predictor():
    df = generate_iot_data(days=30, random_seed=42)
    p = EnergyPredictor(n_estimators=20, random_state=42)
    p.fit(df)
    return p


@pytest.fixture(scope="module")
def sample_features():
    return {
        "hour": 12.0,
        "day_of_week": 1,
        "month": 6,
        "is_weekend": 0,
        "temperature_c": 28.0,
        "demand_kw_lag1": 350.0,
        "demand_kw_lag4": 340.0,
        "demand_kw_rolling_mean": 345.0,
        "irradiance_norm": 0.8,
        "cloud_factor": 0.9,
        "solar_gen_kw_lag1": 220.0,
    }


class TestEnergyPredictorFit:
    def test_is_fitted_after_fit(self, fitted_predictor):
        assert fitted_predictor.is_fitted

    def test_metrics_populated(self, fitted_predictor):
        assert "demand_mae" in fitted_predictor.metrics
        assert "demand_r2" in fitted_predictor.metrics
        assert "solar_mae" in fitted_predictor.metrics
        assert "solar_r2" in fitted_predictor.metrics

    def test_r2_reasonable(self, fitted_predictor):
        # Models should explain at least 70 % of variance
        assert fitted_predictor.metrics["demand_r2"] > 0.70
        assert fitted_predictor.metrics["solar_r2"] > 0.70

    def test_mae_reasonable(self, fitted_predictor):
        # MAE should be below 80 kW for both targets
        assert fitted_predictor.metrics["demand_mae"] < 80.0
        assert fitted_predictor.metrics["solar_mae"] < 80.0


class TestEnergyPredictorPredict:
    def test_predict_demand_returns_float(self, fitted_predictor, sample_features):
        result = fitted_predictor.predict_demand(sample_features)
        assert isinstance(result, float)

    def test_predict_solar_returns_float(self, fitted_predictor, sample_features):
        result = fitted_predictor.predict_solar(sample_features)
        assert isinstance(result, float)

    def test_predict_demand_non_negative(self, fitted_predictor, sample_features):
        assert fitted_predictor.predict_demand(sample_features) >= 0.0

    def test_predict_solar_non_negative(self, fitted_predictor, sample_features):
        assert fitted_predictor.predict_solar(sample_features) >= 0.0

    def test_predict_horizon_returns_dataframe(self, fitted_predictor):
        df = generate_iot_data(days=5, random_seed=1)
        current_row = df.iloc[-1]
        horizon_df = fitted_predictor.predict_horizon(current_row, horizon_steps=4)
        assert isinstance(horizon_df, pd.DataFrame)
        assert len(horizon_df) == 4
        assert "predicted_demand_kw" in horizon_df.columns
        assert "predicted_solar_kw" in horizon_df.columns

    def test_raises_if_not_fitted(self):
        p = EnergyPredictor()
        with pytest.raises(RuntimeError):
            p.predict_demand({"hour": 12})


class TestEnergyPredictorPersistence:
    def test_save_and_load(self, fitted_predictor, tmp_path, sample_features):
        fitted_predictor.save(str(tmp_path))
        loaded = EnergyPredictor.load(str(tmp_path))
        assert loaded.is_fitted
        original_pred = fitted_predictor.predict_demand(sample_features)
        loaded_pred = loaded.predict_demand(sample_features)
        assert abs(original_pred - loaded_pred) < 1e-6
