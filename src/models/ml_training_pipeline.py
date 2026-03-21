"""
ML Training Pipeline with Database Integration.

Handles the complete workflow:
1. Load training data from CSV or database
2. Train energy prediction models
3. Store trained models
4. Evaluate performance
5. Use real-world data for continuous improvement
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import joblib

# Import local modules
from src.models.energy_predictor import EnergyPredictor
from src.models.anomaly_detector import AnomalyDetector
from src.data.database import SensorDatabase
from src.data.training_dataset_generator import TrainingDatasetGenerator


class MLTrainingPipeline:
    """
    Complete ML training pipeline with database integration.

    Handles data loading, model training, evaluation, and persistence.
    Can use both synthetic training data and real database data.
    """

    def __init__(
        self,
        model_dir: str = "models",
        db_path: str = "sensor_data.db"
    ):
        """
        Initialize training pipeline.

        Parameters
        ----------
        model_dir : str
            Directory to save trained models
        db_path : str
            Path to sensor database
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

    def load_training_data_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load training data from CSV file.

        Parameters
        ----------
        csv_path : str
            Path to training dataset CSV

        Returns
        -------
        pd.DataFrame
            Training data
        """
        print(f"Loading training data from {csv_path}...")
        df = pd.read_csv(csv_path, parse_dates=['timestamp'])
        print(f"  ✓ Loaded {len(df):,} samples")
        print(f"  ✓ Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        return df

    def load_training_data_from_database(
        self,
        days: int = 90,
        min_samples: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Load training data from sensor database.

        Parameters
        ----------
        days : int
            Number of days to load
        min_samples : int
            Minimum samples required for training

        Returns
        -------
        pd.DataFrame or None
            Training data if sufficient samples exist, else None
        """
        print(f"Loading training data from database ({days} days)...")

        try:
            with SensorDatabase(self.db_path) as db:
                start_time = datetime.now() - timedelta(days=days)
                df = db.get_readings(start_time=start_time)

            if len(df) < min_samples:
                print(f"  ⚠ Insufficient data: {len(df)} samples (need {min_samples})")
                return None

            print(f"  ✓ Loaded {len(df):,} samples from database")
            print(f"  ✓ Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

            return df

        except Exception as e:
            print(f"  ✗ Error loading from database: {e}")
            return None

    def generate_fresh_training_data(
        self,
        years: int = 2,
        output_csv: bool = True
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Generate fresh synthetic training data.

        Parameters
        ----------
        years : int
            Years of data to generate
        output_csv : bool
            Whether to save to CSV

        Returns
        -------
        tuple
            (DataFrame, csv_path or None)
        """
        print(f"Generating fresh training data ({years} years)...")

        generator = TrainingDatasetGenerator(random_seed=42)
        df = generator.generate_training_dataset(
            start_date="2022-01-01",
            years=years,
            interval_minutes=15
        )

        csv_path = None
        if output_csv:
            csv_path = generator.save_dataset(df)

        return df, csv_path

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for model training.

        Ensures all required columns exist and adds derived features.

        Parameters
        ----------
        df : pd.DataFrame
            Raw training data

        Returns
        -------
        pd.DataFrame
            Feature-ready DataFrame
        """
        print("Preparing features for training...")

        df = df.copy()

        # Ensure timestamp is datetime
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Extract time features if not present
        if 'hour' not in df.columns:
            df['hour'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60.0

        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['timestamp'].dt.dayofweek

        if 'month' not in df.columns:
            df['month'] = df['timestamp'].dt.month

        if 'is_weekend' not in df.columns:
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # Ensure required columns exist
        required_cols = [
            'solar_gen_kw', 'demand_kw', 'temperature_c',
            'irradiance_norm', 'battery_soc_pct'
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Add cloud factor if not present (estimate from solar generation)
        if 'cloud_factor' not in df.columns:
            # Estimate cloud factor from actual vs expected solar
            max_solar = df['solar_gen_kw'].max()
            df['cloud_factor'] = df['solar_gen_kw'] / (max_solar + 1e-6)
            df['cloud_factor'] = df['cloud_factor'].clip(0, 1)

        print(f"  ✓ Features prepared: {len(df)} samples with {len(df.columns)} columns")

        return df

    def train_energy_predictor(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        n_estimators: int = 100
    ) -> Tuple[EnergyPredictor, Dict]:
        """
        Train energy prediction models.

        Parameters
        ----------
        df : pd.DataFrame
            Training data
        test_size : float
            Fraction for test set
        n_estimators : int
            Number of trees in random forest

        Returns
        -------
        tuple
            (trained_model, metrics_dict)
        """
        print("\n" + "=" * 70)
        print("Training Energy Predictor Models")
        print("=" * 70)

        predictor = EnergyPredictor(n_estimators=n_estimators, random_state=42)
        predictor.fit(df, test_size=test_size)

        print(f"\n✓ Training complete!")
        print(f"  Demand Model - MAE: {predictor.metrics['demand_mae']:.2f} kW, R²: {predictor.metrics['demand_r2']:.3f}")
        print(f"  Solar Model  - MAE: {predictor.metrics['solar_mae']:.2f} kW, R²: {predictor.metrics['solar_r2']:.3f}")

        return predictor, predictor.metrics

    def train_anomaly_detector(
        self,
        df: pd.DataFrame,
        contamination: float = 0.01
    ) -> Tuple[AnomalyDetector, Dict]:
        """
        Train anomaly detection model.

        Parameters
        ----------
        df : pd.DataFrame
            Training data
        contamination : float
            Expected anomaly rate

        Returns
        -------
        tuple
            (trained_detector, metrics_dict)
        """
        print("\n" + "=" * 70)
        print("Training Anomaly Detector")
        print("=" * 70)

        detector = AnomalyDetector(contamination=contamination, random_state=42)
        detector.fit(df)

        # Get detection statistics
        df_with_anomalies = detector.predict(df)
        n_ml_anomalies = df_with_anomalies['is_ml_anomaly'].sum()
        n_rule_anomalies = (df_with_anomalies['fault_flags'] != '').sum()
        n_total_anomalies = df_with_anomalies['is_anomaly_any'].sum()

        metrics = {
            'ml_anomalies': int(n_ml_anomalies),
            'rule_based_anomalies': int(n_rule_anomalies),
            'total_anomalies': int(n_total_anomalies),
            'anomaly_rate_pct': float(n_total_anomalies / len(df) * 100)
        }

        print(f"\n✓ Training complete!")
        print(f"  ML Anomalies: {metrics['ml_anomalies']} ({metrics['ml_anomalies']/len(df)*100:.2f}%)")
        print(f"  Rule-based Anomalies: {metrics['rule_based_anomalies']} ({metrics['rule_based_anomalies']/len(df)*100:.2f}%)")
        print(f"  Total Unique: {metrics['total_anomalies']} ({metrics['anomaly_rate_pct']:.2f}%)")

        return detector, metrics

    def save_models(
        self,
        predictor: EnergyPredictor,
        detector: AnomalyDetector,
        prefix: str = "production"
    ) -> Dict[str, str]:
        """
        Save trained models to disk.

        Parameters
        ----------
        predictor : EnergyPredictor
            Trained energy predictor
        detector : AnomalyDetector
            Trained anomaly detector
        prefix : str
            Filename prefix

        Returns
        -------
        dict
            Paths to saved models
        """
        print("\n" + "=" * 70)
        print("Saving Models")
        print("=" * 70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save predictor
        predictor_path = self.model_dir / f"{prefix}_energy_predictor_{timestamp}.pkl"
        predictor.save(str(predictor_path))
        print(f"  ✓ Energy Predictor: {predictor_path}")

        # Save detector
        detector_path = self.model_dir / f"{prefix}_anomaly_detector_{timestamp}.pkl"
        detector.save(str(detector_path))
        print(f"  ✓ Anomaly Detector: {detector_path}")

        # Save metadata
        metadata = {
            'training_timestamp': timestamp,
            'predictor_path': str(predictor_path),
            'detector_path': str(detector_path),
            'predictor_metrics': predictor.metrics,
            'n_samples_trained': len(predictor._demand_model.feature_importances_) if hasattr(predictor._demand_model, 'feature_importances_') else 0
        }

        metadata_path = self.model_dir / f"{prefix}_metadata_{timestamp}.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"  ✓ Metadata: {metadata_path}")

        return {
            'predictor': str(predictor_path),
            'detector': str(detector_path),
            'metadata': str(metadata_path)
        }

    def run_full_pipeline(
        self,
        use_database: bool = False,
        generate_new: bool = True,
        years: int = 2
    ) -> Dict:
        """
        Run complete training pipeline.

        Parameters
        ----------
        use_database : bool
            Try to load data from database first
        generate_new : bool
            Generate new synthetic data if no DB data
        years : int
            Years of data to generate if needed

        Returns
        -------
        dict
            Training results and model paths
        """
        print("\n" + "=" * 80)
        print(" " * 20 + "ML TRAINING PIPELINE")
        print("=" * 80)

        # Step 1: Load or generate data
        df = None

        if use_database:
            df = self.load_training_data_from_database(days=365 * years)

        if df is None and generate_new:
            df, csv_path = self.generate_fresh_training_data(years=years)
        elif df is None:
            raise ValueError("No training data available and generate_new=False")

        # Step 2: Prepare features
        df = self.prepare_features(df)

        # Step 3: Train models
        predictor, pred_metrics = self.train_energy_predictor(df)
        detector, det_metrics = self.train_anomaly_detector(df)

        # Step 4: Save models
        model_paths = self.save_models(predictor, detector)

        # Step 5: Generate report
        results = {
            'success': True,
            'training_samples': len(df),
            'date_range': {
                'start': str(df['timestamp'].min()),
                'end': str(df['timestamp'].max())
            },
            'predictor_metrics': pred_metrics,
            'detector_metrics': det_metrics,
            'model_paths': model_paths
        }

        print("\n" + "=" * 80)
        print("TRAINING PIPELINE COMPLETE")
        print("=" * 80)
        print(f"\n✓ Trained on {results['training_samples']:,} samples")
        print(f"✓ Energy Predictor R² scores: Demand={pred_metrics['demand_r2']:.3f}, Solar={pred_metrics['solar_r2']:.3f}")
        print(f"✓ Anomaly Detector: {det_metrics['anomaly_rate_pct']:.2f}% anomaly rate")
        print(f"✓ Models saved to: {self.model_dir}")

        return results


def bulk_load_training_data_to_database(
    csv_path: str,
    db_path: str = "sensor_data.db",
    batch_size: int = 1000
) -> int:
    """
    Bulk load training data from CSV into database.

    Parameters
    ----------
    csv_path : str
        Path to training data CSV
    db_path : str
        Path to database
    batch_size : int
        Number of rows to insert per batch

    Returns
    -------
    int
        Number of rows inserted
    """
    print(f"\nBulk loading training data to database...")
    print(f"  Source: {csv_path}")
    print(f"  Target: {db_path}")

    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    total_rows = len(df)

    print(f"  Rows to insert: {total_rows:,}")

    with SensorDatabase(db_path) as db:
        inserted = 0

        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]

            for _, row in batch.iterrows():
                reading = {
                    'timestamp': row['timestamp'],
                    'solar_gen_kw': row.get('solar_gen_kw', 0),
                    'battery_voltage': 48.0,  # Nominal for 48V system
                    'battery_soc_pct': row.get('battery_soc_pct', 50),
                    'temperature_c': row.get('temperature_c', 25),
                    'irradiance_norm': row.get('irradiance_norm', 0),
                    'demand_kw': row.get('demand_kw', 0),
                    'grid_import_kw': row.get('grid_import_kw', 0),
                    'grid_export_kw': row.get('grid_export_kw', 0)
                }

                db.insert_reading(reading)
                inserted += 1

            if (i + batch_size) % 10000 == 0 or i + batch_size >= total_rows:
                print(f"    Progress: {min(i + batch_size, total_rows):,} / {total_rows:,} ({min(i + batch_size, total_rows)/total_rows*100:.1f}%)")

    print(f"  ✓ Inserted {inserted:,} readings")
    return inserted


def main():
    """Run ML training pipeline."""
    pipeline = MLTrainingPipeline(model_dir="models", db_path="sensor_data.db")

    # Run full pipeline with fresh data generation
    results = pipeline.run_full_pipeline(
        use_database=False,  # Generate fresh data for training
        generate_new=True,
        years=2  # 2 years of training data
    )

    print("\n" + "=" * 80)
    print("Training Pipeline Results")
    print("=" * 80)
    print(f"\nSamples Trained: {results['training_samples']:,}")
    print(f"Date Range: {results['date_range']['start']} to {results['date_range']['end']}")
    print(f"\nEnergy Predictor Performance:")
    print(f"  Demand - MAE: {results['predictor_metrics']['demand_mae']:.2f} kW, R²: {results['predictor_metrics']['demand_r2']:.3f}")
    print(f"  Solar  - MAE: {results['predictor_metrics']['solar_mae']:.2f} kW, R²: {results['predictor_metrics']['solar_r2']:.3f}")
    print(f"\nAnomaly Detector:")
    print(f"  Total Anomalies: {results['detector_metrics']['total_anomalies']:,}")
    print(f"  Anomaly Rate: {results['detector_metrics']['anomaly_rate_pct']:.2f}%")
    print(f"\nModel Files:")
    for model_type, path in results['model_paths'].items():
        print(f"  {model_type}: {path}")

    print("\n✓ Training complete! Models ready for deployment. 🚀")


if __name__ == "__main__":
    main()
