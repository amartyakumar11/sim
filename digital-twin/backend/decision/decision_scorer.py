"""
Decision Scorer: Deterministic scoring for intervention scenarios.

Scores interventions based on:
1. Operational improvement (swaps, lost swaps reduction)
2. Capacity improvement (pressure reduction)
3. Financial viability (ROI)

NO randomness, NO ML - pure deterministic formula.
"""

from typing import Dict, Optional


class DecisionScorer:
    """
    Score intervention scenarios deterministically.
    
    Multi-criteria scoring:
    - Operational (40%): Lost swaps reduction, swaps increase
    - Capacity (30%): Zone pressure reduction
    - Financial (30%): ROI calculation
    
    Same diff → same score (deterministic).
    """
    
    def __init__(
        self,
        weight_operational: float = 0.4,
        weight_capacity: float = 0.3,
        weight_financial: float = 0.3,
        cost_per_station: float = 100000,
        cost_per_bay: float = 5000,
        cost_per_charger: float = 3000,
        revenue_per_swap: float = 10
    ):
        """
        Initialize decision scorer with weights and cost parameters.
        
        Args:
            weight_operational: Weight for operational score (default 0.4)
            weight_capacity: Weight for capacity score (default 0.3)
            weight_financial: Weight for financial score (default 0.3)
            cost_per_station: Cost to add new station (default $100k)
            cost_per_bay: Cost per additional swap bay (default $5k)
            cost_per_charger: Cost per additional charger (default $3k)
            revenue_per_swap: Revenue per battery swap (default $10)
        """
        # Validate weights sum to 1.0
        total_weight = weight_operational + weight_capacity + weight_financial
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        self.weight_operational = weight_operational
        self.weight_capacity = weight_capacity
        self.weight_financial = weight_financial
        
        self.cost_per_station = cost_per_station
        self.cost_per_bay = cost_per_bay
        self.cost_per_charger = cost_per_charger
        self.revenue_per_swap = revenue_per_swap
    
    def score(
        self,
        scenario_diff: Dict,
        intervention_cost: Optional[float] = None
    ) -> Dict:
        """
        Score intervention scenario deterministically.
        
        Args:
            scenario_diff: Output from ScenarioComparator with:
                - kpi_comparison: KPI deltas
                - zone_comparison: Pressure deltas
                - station_comparison: Station performance
            intervention_cost: Optional manual cost override
            
        Returns:
            {
                "total_score": float (0-100),
                "operational_score": float (0-100),
                "capacity_score": float (0-100),
                "financial_score": float (0-100),
                "breakdown": {detailed metrics}
            }
        """
        # Extract comparison data
        kpi_comp = scenario_diff.get("kpi_comparison", {})
        zone_comp = scenario_diff.get("zone_comparison", {})
        station_comp = scenario_diff.get("station_comparison", {})
        
        # Calculate component scores
        operational_score = self._score_operational(kpi_comp)
        capacity_score = self._score_capacity(zone_comp)
        
        # Calculate cost if not provided
        if intervention_cost is None:
            intervention_cost = self._estimate_cost(station_comp)
        
        financial_score = self._score_financial(kpi_comp, intervention_cost)
        
        # Weighted total score
        total_score = (
            self.weight_operational * operational_score +
            self.weight_capacity * capacity_score +
            self.weight_financial * financial_score
        )
        
        return {
            "total_score": round(total_score, 2),
            "operational_score": round(operational_score, 2),
            "capacity_score": round(capacity_score, 2),
            "financial_score": round(financial_score, 2),
            "breakdown": {
                "intervention_cost": intervention_cost,
                "kpi_deltas": kpi_comp,
                "pressure_reductions": zone_comp
            }
        }
    
    def _score_operational(self, kpi_comp: Dict) -> float:
        """
        Score operational improvement (0-100).
        
        Emphasizes:
        - Lost swaps reduction (primary - 70%)
        - Total swaps increase (secondary - 30%)
        
        Args:
            kpi_comp: KPI comparison dict
            
        Returns:
            Operational score (0-100)
        """
        # Extract KPI deltas
        lost_swaps_data = kpi_comp.get("lost_swaps", {})
        total_swaps_data = kpi_comp.get("total_swaps", {})
        
        baseline_lost = lost_swaps_data.get("baseline", 0)
        delta_lost = lost_swaps_data.get("delta", 0)
        
        baseline_swaps = total_swaps_data.get("baseline", 1)  # Avoid div/0
        delta_swaps = total_swaps_data.get("delta", 0)
        
        # Lost swaps reduction score (higher is better, delta is negative)
        if baseline_lost > 0:
            lost_swaps_pct_reduced = -delta_lost / baseline_lost
        else:
            lost_swaps_pct_reduced = 0
        
        # Swaps increase score
        swaps_pct_increased = delta_swaps / baseline_swaps if baseline_swaps > 0 else 0
        
        # Operational score (weighted combination, scaled to 0-100)
        operational = (
            70 * min(1.0, lost_swaps_pct_reduced) +  # Cap at 100% reduction
            30 * min(0.5, swaps_pct_increased) * 2   # Cap at 50% increase
        )
        
        return max(0, min(100, operational))
    
    def _score_capacity(self, zone_comp: Dict) -> float:
        """
        Score capacity improvement (0-100).
        
        Based on zone pressure peak reductions.
        
        Args:
            zone_comp: Zone pressure comparison dict
            
        Returns:
            Capacity score (0-100)
        """
        if not zone_comp:
            return 0
        
        # Calculate average pressure reduction across all zones
        total_reduction_pct = 0
        zone_count = 0
        
        for zone_id, zone_data in zone_comp.items():
            reduction_pct = zone_data.get("reduction_pct", 0)
            
            # Only count reductions (negative means pressure increased)
            if reduction_pct < 0:  # Reduction is positive impact
                total_reduction_pct += abs(reduction_pct)
                zone_count += 1
        
        if zone_count == 0:
            return 0
        
        # Average reduction percentage
        avg_reduction_pct = total_reduction_pct / zone_count
        
        # Scale to 0-100 (assume 50% reduction is excellent)
        capacity = min(100, (avg_reduction_pct / 50) * 100)
        
        return max(0, capacity)
    
    def _score_financial(self, kpi_comp: Dict, intervention_cost: float) -> float:
        """
        Score financial viability (0-100).
        
        Based on ROI calculation:
        - Cost: Intervention infrastructure cost
        - Benefit: Additional swap revenue (annual)
        
        Args:
            kpi_comp: KPI comparison dict
            intervention_cost: Total intervention cost
            
        Returns:
            Financial score (0-100)
        """
        if intervention_cost <= 0:
            return 0
        
        # Calculate annual benefit from additional swaps
        total_swaps_data = kpi_comp.get("total_swaps", {})
        delta_swaps = total_swaps_data.get("delta", 0)
        
        # Annual revenue (delta swaps * revenue per swap * 365 days)
        annual_benefit = delta_swaps * self.revenue_per_swap * 365
        
        # ROI = benefit / cost
        roi = annual_benefit / intervention_cost if intervention_cost > 0 else 0
        
        # Score based on ROI
        # ROI > 1.0 (break-even in < 1 year) = 100 points
        # ROI = 0.5 (2 year payback) = 50 points
        # Scale linearly
        financial = min(100, roi * 100)
        
        return max(0, financial)
    
    def _estimate_cost(self, station_comp: Dict) -> float:
        """
        Estimate intervention cost from station comparison.
        
        Args:
            station_comp: Station performance comparison
            
        Returns:
            Estimated cost
        """
        total_cost = 0
        
        for station_id, station_data in station_comp.items():
            # New station added
            if not station_data.get("exists_in_baseline", True):
                total_cost += self.cost_per_station
            
            # Modified station (bay or charger changes)
            # Note: This is a rough estimate - real implementation would track intervention details
            if station_data.get("exists_in_baseline", False) and station_data.get("exists_in_intervention", False):
                # Assume average modification cost
                total_cost += self.cost_per_bay * 2  # Rough estimate
        
        return total_cost
