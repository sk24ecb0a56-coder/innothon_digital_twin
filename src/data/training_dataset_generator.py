"""
Training Dataset Generator for Campus Energy ML Models.

Generates large-scale AI-ready training datasets with realistic patterns
matching the hardware prototype specifications. Includes multiple scenarios,
seasonal variations, and edge cases for robust model training.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path


class TrainingDatasetGenerator:
    """
    Generate comprehensive training datasets for energy prediction models.

    Creates datasets with:
    - Multiple years of historical data
    - Seasonal variations (summer/winter patterns)
    - Weekday/weekend patterns
    - Weather variations
    - Special events and anomalies
    - Hardware-realistic constraints
    """

    def __init__(self, random_seed: int = 42):
        self.rng = np.random.default_rng(random_seed)

    def _generate_seasonal_factor(self, month: int) -> Dict[str, float]:
        """Generate seasonal multipliers for demand and solar."""
        # Higher demand in summer (cooling) and winter (heating)
        # Peak solar in summer, lower in winter
        summer_months = [5, 6, 7, 8]  # May-Aug
        winter_months = [11, 12, 1, 2]  # Nov-Feb

        if month in summer_months:
            return {
                'demand_factor': 1.2,  # Higher cooling load
                'solar_factor': 1.3,   # Better solar production
                'temp_base': 32.0      # Higher base temperature
            }
        elif month in winter_months:
            return {
                'demand_factor': 1.15,  # Heating load
                'solar_factor': 0.7,    # Lower solar production
                'temp_base': 18.0       # Lower base temperature
            }
        else:
            return {
                'demand_factor': 1.0,
                'solar_factor': 1.0,
                'temp_base': 25.0
            }

    def _solar_irradiance(self, hour: float, month: int, cloud_factor: float = 1.0) -> float:
        """Calculate solar irradiance with seasonal and cloud variations."""
        if hour < 6 or hour > 20:
            return 0.0

        # Seasonal day length variation
        day_length_factor = 1.0 + 0.2 * np.sin(2 * np.pi * (month - 3) / 12)

        # Base irradiance curve
        peak = np.sin(np.pi * (hour - 6) / 14) * cloud_factor * day_length_factor
        return max(0.0, float(peak))

    def _campus_load_profile(
        self,
        hour: float,
        day_of_week: int,
        month: int,
        is_exam_period: bool = False,
        is_vacation: bool = False
    ) -> float:
        """Generate realistic campus load with various scenarios."""
        is_weekend = day_of_week >= 5
        seasonal = self._generate_seasonal_factor(month)
        base_kw = 200.0
        peak_kw = 500.0

        # Vacation periods have much lower demand
        if is_vacation:
            return base_kw * 0.3 + self.rng.normal(0, 5)

        # Exam periods have extended hours and higher demand
        if is_exam_period:
            peak_kw *= 1.2

        # Weekend profile
        if is_weekend:
            if 8 <= hour <= 18:
                load = base_kw + 0.3 * (peak_kw - base_kw) * np.sin(np.pi * (hour - 8) / 10)
            else:
                load = base_kw * 0.6
        else:
            # Weekday profile with distinct patterns
            if hour < 7:
                load = base_kw * 0.7
            elif 7 <= hour < 9:
                # Morning ramp
                load = base_kw + (peak_kw - base_kw) * (hour - 7) / 2
            elif 9 <= hour < 12:
                load = peak_kw
            elif 12 <= hour < 14:
                # Lunch dip
                load = peak_kw * 0.85
            elif 14 <= hour < 18:
                load = peak_kw
            elif 18 <= hour < 22:
                # Evening decay
                load = base_kw + (peak_kw - base_kw) * (22 - hour) / 4
            else:
                load = base_kw * 0.7

        # Apply seasonal factor
        load *= seasonal['demand_factor']

        # Add realistic noise
        load += self.rng.normal(0, 15)

        return max(50.0, min(700.0, load))

    def _generate_weather_data(self, timestamp: datetime, month: int) -> Dict[str, float]:
        """Generate realistic weather conditions."""
        seasonal = self._generate_seasonal_factor(month)
        hour = timestamp.hour + timestamp.minute / 60.0

        # Temperature variation through day
        temp_variation = 5.0 * np.sin(2 * np.pi * (hour - 6) / 24)
        temperature = seasonal['temp_base'] + temp_variation + self.rng.normal(0, 2)

        # Cloud cover with persistence (clouds don't change instantly)
        cloud_factor = max(0.1, min(1.0, 0.7 + self.rng.normal(0, 0.2)))

        # Irradiance
        irradiance = self._solar_irradiance(hour, month, cloud_factor)

        return {
            'temperature_c': temperature,
            'cloud_factor': cloud_factor,
            'irradiance_norm': irradiance
        }

    def _simulate_battery_and_grid(
        self,
        solar_kw: float,
        demand_kw: float,
        battery_soc_kwh: float,
        battery_capacity_kwh: float,
        interval_hours: float = 0.25
    ) -> Dict[str, float]:
        """Simulate battery charging/discharging and grid interaction."""
        charge_efficiency = 0.95
        discharge_efficiency = 0.95
        max_charge_rate = 100.0  # kW
        max_discharge_rate = 100.0  # kW

        net_power = solar_kw - demand_kw

        if net_power > 0:  # Surplus solar
            # Try to charge battery
            max_charge = min(
                net_power,
                max_charge_rate,
                (battery_capacity_kwh * 0.95 - battery_soc_kwh) / (interval_hours * charge_efficiency)
            )
            battery_charge = max(0, max_charge)
            battery_soc_kwh += battery_charge * interval_hours * charge_efficiency

            # Export remaining to grid
            grid_export = max(0, net_power - battery_charge)
            grid_import = 0

        else:  # Deficit (demand > solar)
            deficit = abs(net_power)

            # Try to discharge battery
            max_discharge = min(
                deficit,
                max_discharge_rate,
                (battery_soc_kwh - battery_capacity_kwh * 0.1) / (interval_hours / discharge_efficiency)
            )
            battery_discharge = max(0, max_discharge)
            battery_soc_kwh -= battery_discharge * interval_hours / discharge_efficiency

            # Import remaining from grid
            grid_import = max(0, deficit - battery_discharge)
            grid_export = 0
            battery_charge = 0

        # Ensure battery stays within bounds
        battery_soc_kwh = max(battery_capacity_kwh * 0.1, min(battery_capacity_kwh * 0.95, battery_soc_kwh))
        battery_soc_pct = (battery_soc_kwh / battery_capacity_kwh) * 100

        return {
            'battery_soc_kwh': battery_soc_kwh,
            'battery_soc_pct': battery_soc_pct,
            'grid_import_kw': grid_import,
            'grid_export_kw': grid_export
        }

    def _inject_anomalies(self, data: Dict, anomaly_prob: float = 0.01) -> Dict:
        """Randomly inject realistic anomalies."""
        if self.rng.random() < anomaly_prob:
            anomaly_type = self.rng.choice([
                'demand_spike',
                'solar_drop',
                'battery_fault',
                'sensor_error'
            ])

            if anomaly_type == 'demand_spike':
                data['demand_kw'] *= self.rng.uniform(1.5, 2.5)
                data['is_anomaly'] = True
                data['anomaly_type'] = 'demand_spike'
            elif anomaly_type == 'solar_drop':
                data['solar_gen_kw'] *= self.rng.uniform(0.2, 0.5)
                data['is_anomaly'] = True
                data['anomaly_type'] = 'solar_underperform'
            elif anomaly_type == 'battery_fault':
                # Simulate rapid battery drain
                data['battery_soc_pct'] = min(data['battery_soc_pct'], 15.0)
                data['is_anomaly'] = True
                data['anomaly_type'] = 'battery_low'
            elif anomaly_type == 'sensor_error':
                # Unrealistic readings
                data['temperature_c'] = self.rng.uniform(-10, 60)
                data['is_anomaly'] = True
                data['anomaly_type'] = 'sensor_error'

        return data

    def _is_special_period(self, date: datetime) -> Tuple[bool, bool]:
        """Determine if date falls in exam period or vacation."""
        month = date.month
        day = date.day

        # Exam periods: Apr 15-30, Nov 15-30
        is_exam = (month == 4 and day >= 15) or (month == 11 and day >= 15)

        # Vacation periods: Dec 15 - Jan 15, May 15 - Jul 15
        is_vacation = (
            (month == 12 and day >= 15) or
            (month == 1 and day <= 15) or
            (month == 5 and day >= 15) or
            (month == 6) or
            (month == 7 and day <= 15)
        )

        return is_exam, is_vacation

    def generate_training_dataset(
        self,
        start_date: str = "2022-01-01",
        years: int = 2,
        interval_minutes: int = 15,
        solar_capacity_kw: float = 300.0,
        battery_capacity_kwh: float = 500.0,
        anomaly_rate: float = 0.01
    ) -> pd.DataFrame:
        """
        Generate comprehensive training dataset with multiple years of data.

        Parameters
        ----------
        start_date : str
            Starting date in ISO format
        years : int
            Number of years to simulate
        interval_minutes : int
            Data sampling interval in minutes
        solar_capacity_kw : float
            Solar panel capacity in kW
        battery_capacity_kwh : float
            Battery storage capacity in kWh
        anomaly_rate : float
            Probability of anomaly injection

        Returns
        -------
        pd.DataFrame
            Training dataset with 10k+ samples
        """
        start = datetime.fromisoformat(start_date)
        days = years * 365
        steps = int(days * 24 * 60 / interval_minutes)

        print(f"Generating {steps:,} data points ({years} years, {interval_minutes}-min intervals)...")

        records = []
        battery_soc_kwh = 0.5 * battery_capacity_kwh  # Start at 50%
        interval_hours = interval_minutes / 60.0

        for i in range(steps):
            timestamp = start + timedelta(minutes=i * interval_minutes)
            hour = timestamp.hour + timestamp.minute / 60.0
            day_of_week = timestamp.weekday()
            month = timestamp.month
            is_weekend = day_of_week >= 5

            # Determine special periods
            is_exam, is_vacation = self._is_special_period(timestamp)

            # Generate weather
            weather = self._generate_weather_data(timestamp, month)

            # Generate solar production
            seasonal = self._generate_seasonal_factor(month)
            solar_base = weather['irradiance_norm'] * solar_capacity_kw * seasonal['solar_factor']
            solar_noise = self.rng.normal(0, 2)
            solar_gen_kw = max(0, min(solar_capacity_kw, solar_base + solar_noise))

            # Generate campus load
            demand_kw = self._campus_load_profile(hour, day_of_week, month, is_exam, is_vacation)

            # Simulate battery and grid
            battery_grid = self._simulate_battery_and_grid(
                solar_gen_kw, demand_kw, battery_soc_kwh, battery_capacity_kwh, interval_hours
            )
            battery_soc_kwh = battery_grid['battery_soc_kwh']

            # Build record
            record = {
                'timestamp': timestamp,
                'hour': hour,
                'day_of_week': day_of_week,
                'month': month,
                'is_weekend': 1 if is_weekend else 0,
                'is_exam_period': 1 if is_exam else 0,
                'is_vacation': 1 if is_vacation else 0,
                'temperature_c': weather['temperature_c'],
                'irradiance_norm': weather['irradiance_norm'],
                'cloud_factor': weather['cloud_factor'],
                'solar_gen_kw': solar_gen_kw,
                'demand_kw': demand_kw,
                'battery_soc_kwh': battery_grid['battery_soc_kwh'],
                'battery_soc_pct': battery_grid['battery_soc_pct'],
                'grid_import_kw': battery_grid['grid_import_kw'],
                'grid_export_kw': battery_grid['grid_export_kw'],
                'is_anomaly': False,
                'anomaly_type': 'none'
            }

            # Inject anomalies
            record = self._inject_anomalies(record, anomaly_rate)

            records.append(record)

            # Progress indicator
            if (i + 1) % 10000 == 0:
                print(f"  Generated {i+1:,} / {steps:,} samples ({(i+1)/steps*100:.1f}%)")

        df = pd.DataFrame(records)
        print(f"\n✓ Dataset generated: {len(df):,} samples")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Anomalies: {df['is_anomaly'].sum()} ({df['is_anomaly'].sum()/len(df)*100:.2f}%)")

        return df

    def save_dataset(self, df: pd.DataFrame, output_dir: str = "data/training") -> str:
        """Save generated dataset to CSV file."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campus_energy_training_data_{timestamp_str}.csv"
        filepath = os.path.join(output_dir, filename)

        df.to_csv(filepath, index=False)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

        print(f"\n✓ Dataset saved to: {filepath}")
        print(f"  File size: {file_size_mb:.2f} MB")
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")

        return filepath

    def generate_dataset_summary(self, df: pd.DataFrame) -> Dict:
        """Generate statistical summary of the dataset."""
        summary = {
            'total_samples': len(df),
            'date_range': {
                'start': str(df['timestamp'].min()),
                'end': str(df['timestamp'].max()),
                'days': (df['timestamp'].max() - df['timestamp'].min()).days
            },
            'solar_generation': {
                'mean_kw': float(df['solar_gen_kw'].mean()),
                'max_kw': float(df['solar_gen_kw'].max()),
                'total_kwh': float(df['solar_gen_kw'].sum() * 0.25)  # 15-min intervals
            },
            'campus_demand': {
                'mean_kw': float(df['demand_kw'].mean()),
                'max_kw': float(df['demand_kw'].max()),
                'total_kwh': float(df['demand_kw'].sum() * 0.25)
            },
            'battery': {
                'mean_soc_pct': float(df['battery_soc_pct'].mean()),
                'cycles': float((df['battery_soc_pct'].diff().abs().sum()) / 200)  # Approximate cycles
            },
            'grid': {
                'total_import_kwh': float(df['grid_import_kw'].sum() * 0.25),
                'total_export_kwh': float(df['grid_export_kw'].sum() * 0.25)
            },
            'anomalies': {
                'count': int(df['is_anomaly'].sum()),
                'percentage': float(df['is_anomaly'].sum() / len(df) * 100)
            },
            'weekday_weekend_split': {
                'weekday_samples': int((df['is_weekend'] == 0).sum()),
                'weekend_samples': int((df['is_weekend'] == 1).sum())
            }
        }

        return summary


def main():
    """Generate and save training dataset."""
    print("=" * 70)
    print("Campus Energy Training Dataset Generator")
    print("=" * 70)
    print()

    generator = TrainingDatasetGenerator(random_seed=42)

    # Generate 2 years of data (70k+ samples at 15-min intervals)
    df = generator.generate_training_dataset(
        start_date="2022-01-01",
        years=2,
        interval_minutes=15,
        solar_capacity_kw=300.0,
        battery_capacity_kwh=500.0,
        anomaly_rate=0.01
    )

    # Save dataset
    filepath = generator.save_dataset(df)

    # Generate summary
    print("\n" + "=" * 70)
    print("Dataset Summary")
    print("=" * 70)
    summary = generator.generate_dataset_summary(df)

    print(f"\nTotal Samples: {summary['total_samples']:,}")
    print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    print(f"Duration: {summary['date_range']['days']} days")
    print(f"\nSolar Generation:")
    print(f"  Mean: {summary['solar_generation']['mean_kw']:.2f} kW")
    print(f"  Peak: {summary['solar_generation']['max_kw']:.2f} kW")
    print(f"  Total: {summary['solar_generation']['total_kwh']:,.0f} kWh")
    print(f"\nCampus Demand:")
    print(f"  Mean: {summary['campus_demand']['mean_kw']:.2f} kW")
    print(f"  Peak: {summary['campus_demand']['max_kw']:.2f} kW")
    print(f"  Total: {summary['campus_demand']['total_kwh']:,.0f} kWh")
    print(f"\nBattery:")
    print(f"  Mean SoC: {summary['battery']['mean_soc_pct']:.1f}%")
    print(f"  Approximate Cycles: {summary['battery']['cycles']:.0f}")
    print(f"\nGrid:")
    print(f"  Total Import: {summary['grid']['total_import_kwh']:,.0f} kWh")
    print(f"  Total Export: {summary['grid']['total_export_kwh']:,.0f} kWh")
    print(f"\nAnomalies: {summary['anomalies']['count']} ({summary['anomalies']['percentage']:.2f}%)")
    print(f"\nData Split:")
    print(f"  Weekday: {summary['weekday_weekend_split']['weekday_samples']:,} samples")
    print(f"  Weekend: {summary['weekday_weekend_split']['weekend_samples']:,} samples")

    print("\n" + "=" * 70)
    print("✓ Training dataset generation complete!")
    print("=" * 70)

    return filepath


if __name__ == "__main__":
    main()
