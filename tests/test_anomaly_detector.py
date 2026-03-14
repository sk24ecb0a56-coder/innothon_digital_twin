"""Unit tests for the anomaly detector."""

import pytest
import pandas as pd
import numpy as np

from src.data.iot_simulator import generate_iot_data
from src.models.anomaly_detector import AnomalyDetector, ANOMALY_FEATURES


@pytest.fixture(scope="module")
def fitted_detector():
    df = generate_iot_data(days=30, random_seed=42)
    det = AnomalyDetector(contamination=0.05, random_state=42)
    det.fit(df)
    return det, df


class TestAnomalyDetectorFit:
    def test_is_fitted_after_fit(self, fitted_detector):
        det, _ = fitted_detector
        assert det.is_fitted

    def test_threshold_set(self, fitted_detector):
        det, _ = fitted_detector
        assert isinstance(det.threshold_, float)

    def test_raises_if_not_fitted(self):
        det = AnomalyDetector()
        df = generate_iot_data(days=3, random_seed=1)
        with pytest.raises(RuntimeError):
            det.predict(df)


class TestAnomalyDetectorPredict:
    def test_predict_returns_dataframe(self, fitted_detector):
        det, df = fitted_detector
        result = det.predict(df)
        assert isinstance(result, pd.DataFrame)

    def test_new_columns_added(self, fitted_detector):
        det, df = fitted_detector
        result = det.predict(df)
        for col in ["anomaly_score", "is_ml_anomaly", "fault_flags", "is_anomaly_any"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_is_ml_anomaly_binary(self, fitted_detector):
        det, df = fitted_detector
        result = det.predict(df)
        assert set(result["is_ml_anomaly"].unique()).issubset({0, 1})

    def test_is_anomaly_any_binary(self, fitted_detector):
        det, df = fitted_detector
        result = det.predict(df)
        assert set(result["is_anomaly_any"].unique()).issubset({0, 1})

    def test_detects_seeded_anomalies(self, fitted_detector):
        det, df = fitted_detector
        result = det.predict(df)
        # At least some of the seeded anomalies should be detected
        if "is_anomaly" in df.columns:
            true_anomalies = df["is_anomaly"] == 1
            detected = result.loc[true_anomalies, "is_anomaly_any"]
            detection_rate = detected.mean()
            assert detection_rate > 0.1, "Anomaly detection rate too low"

    def test_predict_single_returns_dict(self, fitted_detector):
        det, df = fitted_detector
        reading = df[ANOMALY_FEATURES].iloc[0].to_dict()
        result = det.predict_single(reading)
        assert isinstance(result, dict)
        assert "anomaly_score" in result
        assert "is_ml_anomaly" in result

    def test_score_shape(self, fitted_detector):
        det, df = fitted_detector
        scores = det.score(df)
        assert len(scores) == len(df)


class TestAnomalyDetectorPersistence:
    def test_save_and_load(self, fitted_detector, tmp_path):
        det, df = fitted_detector
        det.save(str(tmp_path))
        loaded = AnomalyDetector.load(str(tmp_path))
        assert loaded.is_fitted
        orig_result = det.predict(df.head(10))
        load_result = loaded.predict(df.head(10))
        pd.testing.assert_series_equal(orig_result["is_ml_anomaly"], load_result["is_ml_anomaly"])
