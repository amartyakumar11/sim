"""
Recommendation Generator: Create executive-readable recommendations.

Converts scored interventions into:
1. Ranked priority list
2. Executive narrative (plain English)
3. Implementation recommendations

NO randomness - deterministic text generation from scores.
"""

from typing import Dict, List, Optional
from datetime import datetime


class RecommendationGenerator:
    """
    Generate executive-readable recommendations from scored interventions.
    
    Deterministic text generation - same inputs → same output.
    """
    
    def __init__(self):
        """Initialize recommendation generator."""
        pass
    
    def rank_interventions(self, scenarios: List[Dict]) -> List[Dict]:
        """
        Rank intervention scenarios by total score (descending).
        
        Args:
            scenarios: List of dicts with 'score' key containing score data
            
        Returns:
            Sorted list (highest score first)
        """
        # Sort by total_score (descending)
        ranked = sorted(
            scenarios,
            key=lambda s: s.get("score", {}).get("total_score", 0),
            reverse=True
        )
        
        return ranked
    
    def generate_recommendation(
        self,
        ranked_scenarios: List[Dict],
        baseline_kpis: Optional[Dict] = None
    ) -> str:
        """
        Generate executive recommendation report.
        
        Args:
            ranked_scenarios: Ranked list of intervention scenarios
            baseline_kpis: Optional baseline KPIs for context
            
        Returns:
            Multi-line executive recommendation text
        """
        if not ranked_scenarios:
            return "No intervention scenarios to recommend."
        
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append("EXECUTIVE RECOMMENDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Top recommendation
        top_scenario = ranked_scenarios[0]
        lines.extend(self._generate_top_recommendation(top_scenario))
        lines.append("")
        
        # Alternative options
        if len(ranked_scenarios) > 1:
            lines.append("-" * 60)
            lines.append("ALTERNATIVE OPTIONS")
            lines.append("-" * 60)
            lines.append("")
            
            for i, scenario in enumerate(ranked_scenarios[1:4], start=2):  # Top 2-4
                lines.extend(self._generate_alternative_summary(i, scenario))
                lines.append("")
        
        # Implementation priority
        lines.append("-" * 60)
        lines.append("IMPLEMENTATION PRIORITY")
        lines.append("-" * 60)
        lines.append("")
        lines.extend(self._generate_priority_ranking(ranked_scenarios))
        
        return "\n".join(lines)
    
    def _generate_top_recommendation(self, scenario: Dict) -> List[str]:
        """Generate detailed recommendation for top-ranked scenario."""
        lines = []
        
        intervention = scenario.get("intervention", {})
        score = scenario.get("score", {})
        diff = scenario.get("diff", {})
        
        # Extract intervention details
        intervention_type = intervention.get("intervention_type", "Unknown")
        station_id = intervention.get("station_id", "Unknown")
        
        # Extract scores
        total_score = score.get("total_score", 0)
        operational = score.get("operational_score", 0)
        capacity = score.get("capacity_score", 0)
        financial = score.get("financial_score", 0)
        
        # Extract KPI impacts
        kpi_comp = diff.get("kpi_comparison", {})
        zone_comp = diff.get("zone_comparison", {})
        
        total_swaps = kpi_comp.get("total_swaps", {})
        lost_swaps = kpi_comp.get("lost_swaps", {})
        
        # Recommendation header
        lines.append("🎯 TOP RECOMMENDATION")
        lines.append("")
        
        # Intervention summary
        intervention_name = self._format_intervention_name(intervention)
        lines.append(f"Action: {intervention_name}")
        lines.append(f"Overall Score: {total_score:.1f}/100")
        lines.append(f"Priority: {self._get_priority_label(total_score)}")
        lines.append("")
        
        # Expected impact
        lines.append("EXPECTED IMPACT:")
        
        if total_swaps.get("delta", 0) != 0:
            swaps_delta_pct = total_swaps.get("delta_pct", 0)
            sign = "+" if swaps_delta_pct > 0 else ""
            lines.append(f"  • Swaps: {sign}{swaps_delta_pct:.1f}% ({total_swaps.get('baseline', 0)} → {total_swaps.get('intervention', 0)})")
        
        if lost_swaps.get("delta", 0) != 0:
            lost_delta_pct = lost_swaps.get("delta_pct", 0)
            sign = "+" if lost_delta_pct > 0 else ""
            lines.append(f"  • Lost Swaps: {sign}{lost_delta_pct:.1f}% ({lost_swaps.get('baseline', 0)} → {lost_swaps.get('intervention', 0)})")
        
        # ROI
        cost = score.get("breakdown", {}).get("intervention_cost", 0)
        if cost > 0:
            benefit_annual = (total_swaps.get("delta", 0) * 10 * 365)
            roi = benefit_annual / cost
            payback_months = 12 / roi if roi > 0 else 999
            lines.append(f"  • ROI: {roi:.2f}x (break-even in {payback_months:.0f} months)")
        
        lines.append("")
        
        # Rationale
        lines.append("RATIONALE:")
        lines.extend(self._generate_rationale(intervention, diff, score))
        
        # Score breakdown
        lines.append("")
        lines.append("SCORE BREAKDOWN:")
        lines.append(f"  • Operational Impact: {operational:.1f}/100")
        lines.append(f"  • Capacity Improvement: {capacity:.1f}/100")
        lines.append(f"  • Financial Viability: {financial:.1f}/100")
        
        return lines
    
    def _generate_alternative_summary(self, rank: int, scenario: Dict) -> List[str]:
        """Generate brief summary for alternative option."""
        lines = []
        
        intervention = scenario.get("intervention", {})
        score = scenario.get("score", {})
        
        intervention_name = self._format_intervention_name(intervention)
        total_score = score.get("total_score", 0)
        
        lines.append(f"{rank}. {intervention_name}")
        lines.append(f"   Score: {total_score:.1f}/100")
        lines.append(f"   Priority: {self._get_priority_label(total_score)}")
        
        return lines
    
    def _generate_priority_ranking(self, scenarios: List[Dict]) -> List[str]:
        """Generate implementation priority recommendations."""
        lines = []
        
        for i, scenario in enumerate(scenarios[:5], start=1):  # Top 5
            score = scenario.get("score", {}).get("total_score", 0)
            intervention_name = self._format_intervention_name(scenario.get("intervention", {}))
            
            if score >= 70:
                timing = "Immediate - High priority"
            elif score >= 50:
                timing = "Next quarter - Medium priority"
            else:
                timing = "Long-term consideration"
            
            lines.append(f"{i}. {intervention_name} ({timing})")
        
        return lines
    
    def _generate_rationale(self, intervention: Dict, diff: Dict, score: Dict) -> List[str]:
        """Generate rationale explanation."""
        lines = []
        
        # Identify problem zones
        zone_comp = diff.get("zone_comparison", {})
        high_pressure_zones = [
            (zone, data) for zone, data in zone_comp.items()
            if data.get("baseline_peak", 0) > 10
        ]
        
        if high_pressure_zones:
            zone_id, zone_data = high_pressure_zones[0]
            baseline_peak = zone_data.get("baseline_peak", 0)
            intervention_peak = zone_data.get("intervention_peak", 0)
            
            lines.append(f"  {zone_id} experiences high pressure (peak: {baseline_peak}) during")
            lines.append(f"  peak hours, causing service bottlenecks and lost swaps.")
            lines.append("")
            lines.append(f"  This intervention reduces peak pressure to {intervention_peak}")
            lines.append(f"  ({zone_data.get('reduction_pct', 0):.1f}% reduction), alleviating the bottleneck.")
        else:
            lines.append("  This intervention improves system capacity and operational efficiency")
            lines.append("  through targeted infrastructure enhancements.")
        
        return lines
    
    def _format_intervention_name(self, intervention: Dict) -> str:
        """Format intervention as human-readable name."""
        if isinstance(intervention, dict):
            intervention_type = intervention.get("intervention_type")
            station_id = intervention.get("station_id", "Unknown")
            
            if hasattr(intervention_type, 'value'):
                type_str = intervention_type.value
            else:
                type_str = str(intervention_type)
            
            if type_str == "add_station":
                return f"Add Station {station_id}"
            elif type_str == "remove_station":
                return f"Remove Station {station_id}"
            elif type_str == "modify_capacity":
                return f"Increase Capacity at {station_id}"
            elif type_str == "modify_swap_time":
                return f"Optimize Swap Time at {station_id}"
            elif type_str == "modify_chargers":
                return f"Add Chargers at {station_id}"
            else:
                return f"{type_str} at {station_id}"
        
        return "Unknown Intervention"
    
    def _get_priority_label(self, score: float) -> str:
        """Get priority label from score."""
        if score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "LOW"
