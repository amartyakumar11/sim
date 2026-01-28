"""
Scenario Ranker for Digital Twin Simulation Platform.

Ranks scenarios based on weighted KPI and ROI deltas.
"""

from typing import Dict, List


class ScenarioRanker:
    """
    Ranks scenarios based on weighted score calculation.

    Uses deterministic scoring with stable sorting.
    """

    def __init__(self, diffs: List[dict], weights: dict):
        """
        Initialize scenario ranker.

        Args:
            diffs: List of diff dictionaries (output of ScenarioDiff.compute())
            weights: Weighting configuration dictionary:
                {
                    "avg_wait_time": float,
                    "lost_swaps": float,
                    "throughput": float,
                    "roi": float
                }
                Weights should sum to approximately 1.0 for normalization

        TODO: Add weight validation
        TODO: Add normalization of weights
        TODO: Add custom scoring functions
        """
        self.diffs = diffs
        self.weights = weights

        # TODO: Validate weights sum to 1.0
        # TODO: Add weight normalization

    def rank(self, scenario_ids: List[str] = None) -> List[dict]:
        """
        Rank scenarios based on weighted score.

        Args:
            scenario_ids: Optional list of scenario IDs matching diffs order

        Returns:
            Ranked list of dictionaries:
                [
                    {
                        "scenario_id": str,
                        "score": float,
                        "kpi_deltas": {...},
                        "roi_deltas": {...}
                    }
                ]
                Sorted by score (descending), with tie-breaking by scenario_id

        Score calculation:
            score = (-avg_wait_time_delta * w1)
                  + (-lost_swaps_delta * w2)
                  + (throughput_delta * w3)
                  + (roi_delta * w4)

        Rules:
            - Deterministic ranking
            - Stable sorting (tie-break by scenario_id)
            - No optimization heuristics

        TODO: Add ML-based ranking
        TODO: Add multi-objective optimization ranking
        TODO: Add constraint-based filtering
        """
        if scenario_ids is None:
            scenario_ids = [f"scenario_{i}" for i in range(len(self.diffs))]

        if len(scenario_ids) != len(self.diffs):
            raise ValueError(f"scenario_ids length ({len(scenario_ids)}) must match diffs length ({len(self.diffs)})")

        # Extract weights
        w_wait_time = self.weights.get("avg_wait_time", 0.25)
        w_lost_swaps = self.weights.get("lost_swaps", 0.20)
        w_throughput = self.weights.get("throughput", 0.20)
        w_roi = self.weights.get("roi", 0.35)

        # Calculate scores
        ranked_scenarios = []
        for scenario_id, diff in zip(scenario_ids, self.diffs):
            kpi_deltas = diff.get("kpi_deltas", {})
            roi_deltas = diff.get("roi_deltas", {})

            # Calculate weighted score
            # Negative for wait_time and lost_swaps (lower is better)
            # Positive for throughput and roi (higher is better)
            score = (
                -kpi_deltas.get("avg_wait_time_delta", 0.0) * w_wait_time +
                -kpi_deltas.get("lost_swaps_delta", 0.0) * w_lost_swaps +
                kpi_deltas.get("throughput_delta", 0.0) * w_throughput +
                roi_deltas.get("roi_delta", 0.0) * w_roi
            )

            ranked_scenarios.append({
                "scenario_id": scenario_id,
                "score": score,
                "kpi_deltas": kpi_deltas.copy(),
                "roi_deltas": roi_deltas.copy()
            })

        # Sort by score (descending), then by scenario_id (ascending) for tie-breaking
        ranked_scenarios.sort(key=lambda x: (-x["score"], x["scenario_id"]))

        return ranked_scenarios

    def snapshot(self) -> dict:
        """
        Create a snapshot of ranker metadata.

        Returns:
            Dictionary containing:
                - "num_scenarios": int
                - "weight_config": dict
        """
        return {
            "num_scenarios": len(self.diffs),
            "weight_config": self.weights.copy()
        }
