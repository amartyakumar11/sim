"""
Scenario Diff for Digital Twin Simulation Platform.

Computes differences between baseline and scenario simulation results.
"""

from typing import Dict


class ScenarioDiff:
    """
    Computes KPI and ROI deltas between baseline and scenario results.

    All calculations are pure functions and deterministic.
    """

    def __init__(self, baseline: dict, scenario: dict):
        """
        Initialize scenario diff calculator.

        Args:
            baseline: Baseline simulation result dictionary (output of run_simulation)
            scenario: Scenario simulation result dictionary (output of run_simulation)

        TODO: Add validation for result structure
        TODO: Add support for partial result comparison
        """
        self.baseline = baseline
        self.scenario = scenario

        # TODO: Add result schema validation
        # TODO: Add missing key handling strategies

    def compute(self) -> dict:
        """
        Compute KPI and ROI deltas between baseline and scenario.

        Returns:
            Dictionary containing:
                - "kpi_deltas": dict with KPI differences
                - "roi_deltas": dict with ROI differences

        Rules:
            - Never mutate input dicts
            - All calculations are pure functions
            - Handle missing keys safely (default to 0)
            - Deltas are scenario - baseline

        TODO: Add percentile delta calculations
        TODO: Add timeseries delta calculations
        """
        baseline_kpis = self.baseline.get("kpis", {})
        scenario_kpis = self.scenario.get("kpis", {})

        # Compute KPI deltas
        kpi_deltas = {
            "avg_wait_time_delta": scenario_kpis.get("avg_wait_time", 0.0) - baseline_kpis.get("avg_wait_time", 0.0),
            "lost_swaps_delta": scenario_kpis.get("lost_swaps", 0) - baseline_kpis.get("lost_swaps", 0),
            "utilization_delta": scenario_kpis.get("utilization", 0.0) - baseline_kpis.get("utilization", 0.0),
            "throughput_delta": scenario_kpis.get("throughput", 0) - baseline_kpis.get("throughput", 0),
            "idle_inventory_delta": scenario_kpis.get("idle_inventory", 0.0) - baseline_kpis.get("idle_inventory", 0.0)
        }

        # Compute ROI deltas
        roi_deltas = {
            "revenue_delta": scenario_kpis.get("revenue", 0.0) - baseline_kpis.get("revenue", 0.0),
            "operational_cost_delta": scenario_kpis.get("operational_cost", 0.0) - baseline_kpis.get("operational_cost", 0.0),
            "net_profit_delta": scenario_kpis.get("net_profit", 0.0) - baseline_kpis.get("net_profit", 0.0),
            "roi_delta": scenario_kpis.get("roi", 0.0) - baseline_kpis.get("roi", 0.0)
        }

        return {
            "kpi_deltas": kpi_deltas,
            "roi_deltas": roi_deltas
        }

    def snapshot(self) -> dict:
        """
        Create a snapshot of diff metadata.

        Returns:
            Dictionary containing:
                - "baseline_run_id": str
                - "scenario_run_id": str
        """
        baseline_metadata = self.baseline.get("metadata", {})
        scenario_metadata = self.scenario.get("metadata", {})

        return {
            "baseline_run_id": baseline_metadata.get("run_id", "unknown"),
            "scenario_run_id": scenario_metadata.get("run_id", "unknown")
        }
