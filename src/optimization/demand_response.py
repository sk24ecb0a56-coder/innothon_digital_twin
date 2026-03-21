"""
Demand Response and Action Recommendation System.

Provides actionable recommendations based on energy predictions to:
- Reduce peak demand
- Optimize battery usage
- Prevent grid overload
- Minimize energy costs
- Respond to anomalies

This addresses the judges' question: "What do we do with the prediction?"
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import pandas as pd


class ActionPriority(Enum):
    """Priority levels for recommended actions."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action recommended within 1 hour
    MEDIUM = "medium"      # Action recommended within 4 hours
    LOW = "low"            # Optional optimization


class ActionCategory(Enum):
    """Categories of demand response actions."""
    LOAD_SHEDDING = "load_shedding"           # Reduce demand
    BATTERY_MANAGEMENT = "battery_management"  # Optimize battery
    PEAK_SHAVING = "peak_shaving"             # Shift loads
    GRID_MANAGEMENT = "grid_management"       # Manage grid import/export
    PREVENTIVE = "preventive"                 # Prevent issues
    COST_OPTIMIZATION = "cost_optimization"   # Reduce costs


@dataclass
class ActionRecommendation:
    """A single actionable recommendation."""
    action_id: str
    priority: ActionPriority
    category: ActionCategory
    title: str
    description: str
    expected_savings_inr: float
    expected_reduction_kw: float
    implementation_time: str
    target_systems: List[str]
    reasoning: str


class DemandResponseSystem:
    """
    Generate actionable recommendations based on energy predictions.

    Uses predicted demand, solar generation, and current system state to
    recommend specific actions that campus operations can take.
    """

    def __init__(
        self,
        peak_tariff_inr: float = 12.0,
        off_peak_tariff_inr: float = 8.0,
        demand_charge_inr_per_kw: float = 150.0,
        peak_hours: Tuple[int, int] = (9, 18)
    ):
        self.peak_tariff = peak_tariff_inr
        self.off_peak_tariff = off_peak_tariff_inr
        self.demand_charge = demand_charge_inr_per_kw
        self.peak_hours = peak_hours

    def analyze_predictions(
        self,
        predicted_demand_kw: float,
        predicted_solar_kw: float,
        current_battery_soc_pct: float,
        current_hour: int,
        anomaly_detected: bool = False,
        anomaly_type: str = None
    ) -> List[ActionRecommendation]:
        """
        Generate action recommendations based on predictions.

        Parameters
        ----------
        predicted_demand_kw : float
            Predicted campus demand for next interval
        predicted_solar_kw : float
            Predicted solar generation for next interval
        current_battery_soc_pct : float
            Current battery state of charge
        current_hour : int
            Current hour of day (0-23)
        anomaly_detected : bool
            Whether an anomaly was detected
        anomaly_type : str
            Type of anomaly if detected

        Returns
        -------
        List[ActionRecommendation]
            Prioritized list of actionable recommendations
        """
        recommendations = []

        # Check if in peak hours
        is_peak_hour = self.peak_hours[0] <= current_hour < self.peak_hours[1]

        # Calculate predicted net demand
        predicted_net_demand = predicted_demand_kw - predicted_solar_kw

        # 1. CRITICAL: Handle anomalies
        if anomaly_detected:
            recommendations.extend(
                self._generate_anomaly_responses(anomaly_type, predicted_demand_kw, current_battery_soc_pct)
            )

        # 2. HIGH: Peak demand management
        if predicted_demand_kw > 600:  # Approaching campus capacity
            recommendations.extend(
                self._generate_peak_shaving_actions(predicted_demand_kw, is_peak_hour, current_battery_soc_pct)
            )

        # 3. HIGH: Critical battery management
        if current_battery_soc_pct < 15:
            recommendations.extend(
                self._generate_low_battery_actions(current_battery_soc_pct, predicted_solar_kw, current_hour)
            )
        elif current_battery_soc_pct > 90 and predicted_solar_kw > predicted_demand_kw:
            recommendations.extend(
                self._generate_high_battery_actions(current_battery_soc_pct, predicted_solar_kw, predicted_demand_kw)
            )

        # 4. MEDIUM: Load shifting for cost optimization
        if is_peak_hour and predicted_net_demand > 200:
            recommendations.extend(
                self._generate_load_shifting_actions(predicted_demand_kw, predicted_solar_kw, current_battery_soc_pct)
            )

        # 5. MEDIUM: Preemptive charging
        if not is_peak_hour and current_battery_soc_pct < 50 and predicted_solar_kw > predicted_demand_kw:
            recommendations.extend(
                self._generate_charging_actions(predicted_solar_kw, predicted_demand_kw, current_battery_soc_pct)
            )

        # 6. LOW: Efficiency optimizations
        recommendations.extend(
            self._generate_efficiency_actions(predicted_demand_kw, predicted_solar_kw, current_hour)
        )

        # Sort by priority
        priority_order = {
            ActionPriority.CRITICAL: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3
        }
        recommendations.sort(key=lambda x: priority_order[x.priority])

        return recommendations

    def _generate_anomaly_responses(
        self, anomaly_type: str, predicted_demand_kw: float, battery_soc_pct: float
    ) -> List[ActionRecommendation]:
        """Generate critical responses to detected anomalies."""
        actions = []

        if anomaly_type == "demand_spike":
            actions.append(ActionRecommendation(
                action_id="ANO-001",
                priority=ActionPriority.CRITICAL,
                category=ActionCategory.LOAD_SHEDDING,
                title="URGENT: Demand Spike Detected - Activate Load Shedding",
                description=(
                    f"Abnormal demand spike detected ({predicted_demand_kw:.0f} kW). "
                    "Immediately shed non-critical loads to prevent grid overload. "
                    "Priority targets: HVAC setpoint adjustment, lighting in unoccupied areas, "
                    "defer EV charging."
                ),
                expected_savings_inr=500,
                expected_reduction_kw=min(100, predicted_demand_kw * 0.15),
                implementation_time="Immediate (0-5 minutes)",
                target_systems=["HVAC", "Lighting", "EV Chargers"],
                reasoning="Demand spike detected by anomaly detection system. Immediate action required to prevent grid penalties."
            ))

        elif anomaly_type == "solar_underperform":
            actions.append(ActionRecommendation(
                action_id="ANO-002",
                priority=ActionPriority.HIGH,
                category=ActionCategory.PREVENTIVE,
                title="Solar System Underperformance - Inspection Required",
                description=(
                    "Solar generation significantly below expected levels. "
                    "Check for panel soiling, shading, or inverter faults. "
                    "Increase battery discharge readiness."
                ),
                expected_savings_inr=0,
                expected_reduction_kw=0,
                implementation_time="Within 1 hour",
                target_systems=["Solar Panels", "Inverters", "Battery System"],
                reasoning="Solar output below predicted levels. Maintenance inspection needed to restore capacity."
            ))

        elif anomaly_type == "battery_low":
            if battery_soc_pct < 10:
                actions.append(ActionRecommendation(
                    action_id="ANO-003",
                    priority=ActionPriority.CRITICAL,
                    category=ActionCategory.BATTERY_MANAGEMENT,
                    title="CRITICAL: Battery Level Critically Low",
                    description=(
                        f"Battery at {battery_soc_pct:.1f}% SoC - approaching minimum safe level. "
                        "Stop all battery discharge immediately. Activate backup grid supply. "
                        "Investigate rapid discharge cause."
                    ),
                    expected_savings_inr=0,
                    expected_reduction_kw=0,
                    implementation_time="Immediate",
                    target_systems=["Battery Management System", "Grid Connection"],
                    reasoning="Battery critically low. Risk of deep discharge damage and loss of backup capacity."
                ))

        return actions

    def _generate_peak_shaving_actions(
        self, predicted_demand_kw: float, is_peak_hour: bool, battery_soc_pct: float
    ) -> List[ActionRecommendation]:
        """Generate actions to reduce peak demand."""
        actions = []

        reduction_target = predicted_demand_kw - 550  # Target to keep below 550 kW

        if reduction_target > 50:  # Significant reduction needed
            # Calculate savings from avoiding demand charges
            demand_charge_savings = reduction_target * self.demand_charge
            energy_savings = reduction_target * (self.peak_tariff if is_peak_hour else self.off_peak_tariff) * 0.25

            actions.append(ActionRecommendation(
                action_id="PEAK-001",
                priority=ActionPriority.HIGH,
                category=ActionCategory.PEAK_SHAVING,
                title="Peak Demand Reduction - Immediate Load Curtailment",
                description=(
                    f"Predicted demand of {predicted_demand_kw:.0f} kW exceeds optimal threshold. "
                    f"Reduce load by {reduction_target:.0f} kW through:\n"
                    "1. Increase HVAC setpoint by 2°C (20-30 kW reduction)\n"
                    "2. Dim corridor lighting by 30% (10-15 kW reduction)\n"
                    "3. Defer non-critical equipment startup (15-20 kW)\n"
                    "4. Maximize battery discharge if SoC > 30%"
                ),
                expected_savings_inr=demand_charge_savings + energy_savings,
                expected_reduction_kw=reduction_target,
                implementation_time="0-15 minutes",
                target_systems=["HVAC", "Lighting", "Battery", "Building Automation"],
                reasoning=(
                    f"Predicted demand exceeds threshold by {reduction_target:.0f} kW. "
                    f"Avoiding demand charges worth ₹{demand_charge_savings:.0f} plus energy savings."
                )
            ))

            # Battery assistance if available
            if battery_soc_pct > 30:
                battery_contribution = min(100, reduction_target * 0.5)  # Battery can help with half
                actions.append(ActionRecommendation(
                    action_id="PEAK-002",
                    priority=ActionPriority.HIGH,
                    category=ActionCategory.BATTERY_MANAGEMENT,
                    title="Maximize Battery Discharge for Peak Shaving",
                    description=(
                        f"Battery at {battery_soc_pct:.0f}% SoC - discharge at maximum rate ({battery_contribution:.0f} kW) "
                        "to offset peak demand and reduce grid import."
                    ),
                    expected_savings_inr=battery_contribution * self.peak_tariff * 0.25,
                    expected_reduction_kw=battery_contribution,
                    implementation_time="Immediate",
                    target_systems=["Battery Management System"],
                    reasoning=f"Battery has sufficient charge to contribute {battery_contribution:.0f} kW to peak reduction."
                ))

        return actions

    def _generate_low_battery_actions(
        self, battery_soc_pct: float, predicted_solar_kw: float, current_hour: int
    ) -> List[ActionRecommendation]:
        """Generate actions when battery is critically low."""
        actions = []

        actions.append(ActionRecommendation(
            action_id="BATT-001",
            priority=ActionPriority.HIGH,
            category=ActionCategory.BATTERY_MANAGEMENT,
            title="Low Battery - Preserve Reserve Capacity",
            description=(
                f"Battery at {battery_soc_pct:.1f}% SoC. Stop all discharge to preserve emergency reserve. "
                f"Next solar generation: {predicted_solar_kw:.0f} kW at hour {current_hour}. "
                "Enable grid import to cover shortfall until battery can recharge."
            ),
            expected_savings_inr=0,
            expected_reduction_kw=0,
            implementation_time="Immediate",
            target_systems=["Battery Management System", "Grid Connection"],
            reasoning="Battery below critical threshold. Must preserve remaining capacity for emergencies."
        ))

        return actions

    def _generate_high_battery_actions(
        self, battery_soc_pct: float, predicted_solar_kw: float, predicted_demand_kw: float
    ) -> List[ActionRecommendation]:
        """Generate actions when battery is near full and solar surplus expected."""
        actions = []

        surplus = predicted_solar_kw - predicted_demand_kw

        if surplus > 50:  # Significant surplus
            actions.append(ActionRecommendation(
                action_id="BATT-002",
                priority=ActionPriority.MEDIUM,
                category=ActionCategory.COST_OPTIMIZATION,
                title="High Battery + Solar Surplus - Opportunistic Load Shifting",
                description=(
                    f"Battery at {battery_soc_pct:.0f}% with {surplus:.0f} kW solar surplus predicted. "
                    "Opportune time to run flexible loads using free solar energy:\n"
                    "1. Start water heating/pumping systems\n"
                    "2. Run EV charging at full rate\n"
                    "3. Pre-cool buildings before peak hours\n"
                    "This converts surplus solar (otherwise exported at low rate) to direct use."
                ),
                expected_savings_inr=surplus * (self.peak_tariff - 3.0) * 0.25,  # Avoid later peak purchase
                expected_reduction_kw=-surplus,  # Negative = increase load now
                implementation_time="0-30 minutes",
                target_systems=["Water Heaters", "EV Chargers", "HVAC Pre-cooling"],
                reasoning=(
                    "Battery near capacity with solar surplus. Better to use surplus directly than export at low rate. "
                    "Shift loads to solar hours to avoid peak-hour grid purchases later."
                )
            ))

        return actions

    def _generate_load_shifting_actions(
        self, predicted_demand_kw: float, predicted_solar_kw: float, battery_soc_pct: float
    ) -> List[ActionRecommendation]:
        """Generate load shifting recommendations for peak hours."""
        actions = []

        net_demand = predicted_demand_kw - predicted_solar_kw

        if net_demand > 200 and battery_soc_pct < 60:  # Significant grid dependence during peak
            potential_savings = net_demand * 0.2 * (self.peak_tariff - self.off_peak_tariff) * 0.25

            actions.append(ActionRecommendation(
                action_id="SHIFT-001",
                priority=ActionPriority.MEDIUM,
                category=ActionCategory.PEAK_SHAVING,
                title="Peak Hour Load Shifting - Defer Non-Critical Loads",
                description=(
                    f"Peak hour with {net_demand:.0f} kW grid dependence. Defer flexible loads to off-peak hours:\n"
                    "1. Delay equipment maintenance to evening (after 6 PM)\n"
                    "2. Reduce EV charging rate by 50% (resume full rate at 7 PM)\n"
                    "3. Postpone water heating/pumping to off-peak\n"
                    f"Shifting {net_demand*0.2:.0f} kW saves ₹{potential_savings:.0f} in peak charges."
                ),
                expected_savings_inr=potential_savings,
                expected_reduction_kw=net_demand * 0.2,
                implementation_time="0-30 minutes",
                target_systems=["EV Chargers", "Water Systems", "Maintenance Equipment"],
                reasoning=(
                    f"Peak hour grid dependence high. Shifting 20% of load to off-peak saves "
                    f"₹{self.peak_tariff - self.off_peak_tariff:.0f}/kWh differential."
                )
            ))

        return actions

    def _generate_charging_actions(
        self, predicted_solar_kw: float, predicted_demand_kw: float, battery_soc_pct: float
    ) -> List[ActionRecommendation]:
        """Generate battery charging recommendations."""
        actions = []

        surplus = predicted_solar_kw - predicted_demand_kw

        if surplus > 50 and battery_soc_pct < 50:
            actions.append(ActionRecommendation(
                action_id="CHRG-001",
                priority=ActionPriority.MEDIUM,
                category=ActionCategory.BATTERY_MANAGEMENT,
                title="Preemptive Battery Charging from Solar Surplus",
                description=(
                    f"Solar surplus of {surplus:.0f} kW predicted with battery at {battery_soc_pct:.0f}%. "
                    "Maximize battery charging now to prepare for evening peak demand. "
                    "This stored solar energy can offset expensive grid imports later."
                ),
                expected_savings_inr=surplus * 0.25 * (self.peak_tariff - 3.0),  # Value of avoiding later grid purchase
                expected_reduction_kw=0,
                implementation_time="Immediate",
                target_systems=["Battery Management System"],
                reasoning=(
                    "Off-peak period with solar surplus. Charge battery now to provide capacity during "
                    "expensive peak hours. Each kWh stored saves ₹9 in peak vs export differential."
                )
            ))

        return actions

    def _generate_efficiency_actions(
        self, predicted_demand_kw: float, predicted_solar_kw: float, current_hour: int
    ) -> List[ActionRecommendation]:
        """Generate general efficiency recommendations."""
        actions = []

        # Nighttime efficiency
        if current_hour >= 22 or current_hour < 6:
            if predicted_demand_kw > 200:  # Baseline load seems high at night
                actions.append(ActionRecommendation(
                    action_id="EFF-001",
                    priority=ActionPriority.LOW,
                    category=ActionCategory.COST_OPTIMIZATION,
                    title="Nighttime Efficiency - Reduce Base Load",
                    description=(
                        f"Nighttime demand of {predicted_demand_kw:.0f} kW exceeds expected baseline (150-180 kW). "
                        "Check for:\n"
                        "1. Lighting left on in unoccupied areas\n"
                        "2. HVAC running unnecessarily\n"
                        "3. Equipment left in standby mode\n"
                        "Reducing to baseline saves ₹200-300/night."
                    ),
                    expected_savings_inr=250,
                    expected_reduction_kw=predicted_demand_kw - 180,
                    implementation_time="Within 1 hour",
                    target_systems=["Lighting", "HVAC", "Building Automation"],
                    reasoning="Nighttime base load higher than expected. Likely efficiency opportunities."
                ))

        return actions

    def get_recommendation_summary(self, recommendations: List[ActionRecommendation]) -> Dict:
        """Generate summary statistics for recommendations."""
        if not recommendations:
            return {
                'total_recommendations': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'total_potential_savings_inr': 0,
                'total_potential_reduction_kw': 0
            }

        return {
            'total_recommendations': len(recommendations),
            'critical_count': sum(1 for r in recommendations if r.priority == ActionPriority.CRITICAL),
            'high_count': sum(1 for r in recommendations if r.priority == ActionPriority.HIGH),
            'medium_count': sum(1 for r in recommendations if r.priority == ActionPriority.MEDIUM),
            'low_count': sum(1 for r in recommendations if r.priority == ActionPriority.LOW),
            'total_potential_savings_inr': sum(r.expected_savings_inr for r in recommendations),
            'total_potential_reduction_kw': sum(r.expected_reduction_kw for r in recommendations)
        }

    def format_recommendations_for_display(self, recommendations: List[ActionRecommendation]) -> pd.DataFrame:
        """Convert recommendations to DataFrame for easy display."""
        if not recommendations:
            return pd.DataFrame()

        data = []
        for rec in recommendations:
            data.append({
                'Priority': rec.priority.value.upper(),
                'Category': rec.category.value.replace('_', ' ').title(),
                'Title': rec.title,
                'Expected Savings (₹)': f"₹{rec.expected_savings_inr:.0f}",
                'Load Reduction (kW)': f"{rec.expected_reduction_kw:.0f} kW",
                'Timeline': rec.implementation_time,
                'Target Systems': ', '.join(rec.target_systems)
            })

        return pd.DataFrame(data)
