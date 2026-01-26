"""
Scenario Manager for Digital Twin Simulation Platform.

Manages running multiple simulation scenarios and comparing results.
"""

from typing import Dict, List
from .main import run_simulation
from .event_logger import EventLogger


class ScenarioManager:
    """
    Manages running baseline and intervention scenarios.

    Validates scenario configurations and orchestrates simulation runs.
    """

    def __init__(self, base_config: dict, scenarios: List[dict], event_logger: EventLogger = None):
        """
        Initialize scenario manager.

        Args:
            base_config: Baseline simulation configuration dictionary
            scenarios: List of scenario configuration dictionaries
            event_logger: Optional EventLogger instance for logging scenario events

        Raises:
            ValueError: If scenarios don't match baseline city, seed, or time window

        TODO: Add scenario validation rules
        TODO: Add scenario caching support
        TODO: Add parallel execution support
        """
        self.base_config = base_config
        self.scenarios = scenarios
        self.event_logger = event_logger

        # Validate scenarios match baseline
        self._validate_scenarios()

        # TODO: Add scenario metadata tracking
        # TODO: Add scenario dependency resolution

    def _validate_scenarios(self) -> None:
        """
        Validate that all scenarios match baseline configuration.

        Raises:
            ValueError: If any scenario doesn't match baseline city, seed, or time window
        """
        base_city = self.base_config.get("city")
        base_seed = self.base_config.get("seed")
        base_start_time = self.base_config.get("start_time")
        base_end_time = self.base_config.get("end_time")

        for i, scenario in enumerate(self.scenarios):
            # Merge scenario with base_config to get final config
            merged_config = {**self.base_config, **scenario}
            
            scenario_city = merged_config.get("city")
            scenario_seed = merged_config.get("seed")
            scenario_start_time = merged_config.get("start_time")
            scenario_end_time = merged_config.get("end_time")

            if scenario_city != base_city:
                raise ValueError(
                    f"Scenario {i} city mismatch: baseline={base_city}, scenario={scenario_city}"
                )

            if scenario_seed != base_seed:
                raise ValueError(
                    f"Scenario {i} seed mismatch: baseline={base_seed}, scenario={scenario_seed}"
                )

            if scenario_start_time != base_start_time:
                raise ValueError(
                    f"Scenario {i} start_time mismatch: baseline={base_start_time}, scenario={scenario_start_time}"
                )

            if scenario_end_time != base_end_time:
                raise ValueError(
                    f"Scenario {i} end_time mismatch: baseline={base_end_time}, scenario={scenario_end_time}"
                )

    def run_all(self, mode: str = "fake") -> dict:
        """
        Run baseline and all scenario simulations.

        Args:
            mode: Simulation mode - "fake" (fast, UI-safe) or "real" (full SimPy simulation)

        Returns:
            Dictionary containing:
                - "baseline": baseline simulation result
                - "scenarios": list of scenario results with scenario_id, config, and result

        TODO: Add progress tracking
        TODO: Add error handling per scenario
        TODO: Add scenario cancellation support
        """
        # Validate mode
        if mode not in ("fake", "real"):
            raise ValueError("mode must be 'fake' or 'real'")
        
        if self.event_logger:
            self.event_logger.log_event(
                event_type="rider_arrival",  # Using closest match - scenario_run_started not in schema
                metadata={
                    "event_category": "scenario_run_started",
                    "num_scenarios": len(self.scenarios),
                    "mode": mode
                }
            )

        # Run baseline simulation with specified mode
        baseline_result = run_simulation(self.base_config, mode=mode)

        # Run all scenario simulations
        scenario_results = []
        for scenario in self.scenarios:
            scenario_id = scenario.get("scenario_id", f"scenario_{len(scenario_results)}")
            
            # Merge base_config with scenario overrides
            scenario_config = {**self.base_config, **scenario}

            # Run scenario simulation with specified mode
            scenario_result = run_simulation(scenario_config, mode=mode)

            scenario_results.append({
                "scenario_id": scenario_id,
                "config": scenario,
                "result": scenario_result
            })

        if self.event_logger:
            self.event_logger.log_event(
                event_type="swap_complete",  # Using closest match - scenario_run_completed not in schema
                metadata={
                    "event_category": "scenario_run_completed",
                    "num_scenarios": len(self.scenarios)
                }
            )

        return {
            "baseline": baseline_result,
            "scenarios": scenario_results
        }

    def snapshot(self) -> dict:
        """
        Create a snapshot of scenario manager metadata.

        Returns:
            Dictionary containing:
                - "baseline_city": str
                - "num_scenarios": int
                - "scenario_ids": list[str]
        """
        scenario_ids = [
            scenario.get("scenario_id", f"scenario_{i}")
            for i, scenario in enumerate(self.scenarios)
        ]

        return {
            "baseline_city": self.base_config.get("city", "unknown"),
            "num_scenarios": len(self.scenarios),
            "scenario_ids": scenario_ids
        }
