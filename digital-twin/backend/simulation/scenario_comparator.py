"""
Scenario Comparator: Compare baseline vs intervention scenario outcomes.

Deterministic comparison of simulation results:
- Same seed, same arrivals
- Different graphs (baseline vs intervention)
- Compare KPIs, metrics, pressure signals

NO new events, NO randomness.
"""

from typing import Dict, List, Optional
from datetime import datetime


class ScenarioComparator:
    """
    Compare baseline and intervention scenario outcomes.
    
    Deterministic comparison - same inputs always produce same delta.
    """
    
    def __init__(self):
        """Initialize comparator."""
        pass
    
    def compare_kpis(
        self,
        baseline_kpis: Dict,
        intervention_kpis: Dict
    ) -> Dict:
        """
        Compare KPIs between baseline and intervention scenarios.
        
        Args:
            baseline_kpis: KPIs from baseline run
            intervention_kpis: KPIs from intervention run
            
        Returns:
            Dictionary with delta metrics
            
        Example:
            {
                "total_swaps": {"baseline": 150, "intervention": 165, "delta": +15, "delta_pct": +10.0},
                "lost_swaps": {"baseline": 12, "intervention": 5, "delta": -7, "delta_pct": -58.3}
            }
        """
        comparison = {}
        
        # Get all KPI keys from both scenarios
        all_keys = set(baseline_kpis.keys()) | set(intervention_kpis.keys())
        
        for key in all_keys:
            baseline_val = baseline_kpis.get(key, 0)
            intervention_val = intervention_kpis.get(key, 0)
            
            delta = intervention_val - baseline_val
            delta_pct = (delta / baseline_val * 100) if baseline_val != 0 else 0
            
            comparison[key] = {
                "baseline": baseline_val,
                "intervention": intervention_val,
                "delta": delta,
                "delta_pct": round(delta_pct, 2)
            }
        
        return comparison
    
    def compare_zone_pressure(
        self,
        baseline_pressure: List[Dict],
        intervention_pressure: List[Dict]
    ) -> Dict:
        """
        Compare zone pressure between scenarios.
        
        Args:
            baseline_pressure: Zone pressure from baseline (list of records)
            intervention_pressure: Zone pressure from intervention
            
        Returns:
            Dictionary mapping zone_id to pressure comparison
            
        Example:
            {
                "zone_01": {
                    "baseline_peak": 15,
                    "intervention_peak": 8,
                    "pressure_reduced": True,
                    "reduction_pct": -46.7
                }
            }
        """
        # Aggregate peak pressure per zone for baseline
        baseline_peaks = {}
        for record in baseline_pressure:
            zone = record["zone"]
            score = record["pressure_score"]
            if zone not in baseline_peaks or score > baseline_peaks[zone]:
                baseline_peaks[zone] = score
        
        # Aggregate peak pressure per zone for intervention
        intervention_peaks = {}
        for record in intervention_pressure:
            zone = record["zone"]
            score = record["pressure_score"]
            if zone not in intervention_peaks or score > intervention_peaks[zone]:
                intervention_peaks[zone] = score
        
        # Compare
        comparison = {}
        all_zones = set(baseline_peaks.keys()) | set(intervention_peaks.keys())
        
        for zone in all_zones:
            baseline_peak = baseline_peaks.get(zone, 0)
            intervention_peak = intervention_peaks.get(zone, 0)
            
            delta = intervention_peak - baseline_peak
            delta_pct = (delta / baseline_peak * 100) if baseline_peak != 0 else 0
            
            comparison[zone] = {
                "baseline_peak": baseline_peak,
                "intervention_peak": intervention_peak,
                "pressure_reduced": delta < 0,
                "reduction_pct": round(delta_pct, 2)
            }
        
        return comparison
    
    def compare_station_performance(
        self,
        baseline_timelines: Dict,
        intervention_timelines: Dict
    ) -> Dict:
        """
        Compare station performance between scenarios.
        
        Args:
            baseline_timelines: Station timelines from baseline
            intervention_timelines: Station timelines from intervention
            
        Returns:
            Dictionary mapping station_id to performance comparison
        """
        comparison = {}
        all_stations = set(baseline_timelines.keys()) | set(intervention_timelines.keys())
        
        for station_id in all_stations:
            baseline_data = baseline_timelines.get(station_id, {
                "swaps_total": 0,
                "lost_swaps": 0
            })
            intervention_data = intervention_timelines.get(station_id, {
                "swaps_total": 0,
                "lost_swaps": 0
            })
            
            baseline_swaps = baseline_data.get("swaps_total", 0)
            intervention_swaps = intervention_data.get("swaps_total", 0)
            baseline_lost = baseline_data.get("lost_swaps", 0)
            intervention_lost = intervention_data.get("lost_swaps", 0)
            
            comparison[station_id] = {
                "swaps": {
                    "baseline": baseline_swaps,
                    "intervention": intervention_swaps,
                    "delta": intervention_swaps - baseline_swaps
                },
                "lost_swaps": {
                    "baseline": baseline_lost,
                    "intervention": intervention_lost,
                    "delta": intervention_lost - baseline_lost
                },
                "exists_in_baseline": station_id in baseline_timelines,
                "exists_in_intervention": station_id in intervention_timelines
            }
        
        return comparison
    
    def generate_summary(
        self,
        kpi_comparison: Dict,
        zone_comparison: Dict,
        station_comparison: Dict
    ) -> str:
        """
        Generate human-readable summary of scenario comparison.
        
        Args:
            kpi_comparison: Output from compare_kpis()
            zone_comparison: Output from compare_zone_pressure()
            station_comparison: Output from compare_station_performance()
            
        Returns:
            Multi-line summary string (deterministic)
        """
        lines = []
        
        # KPI summary
        lines.append("=== KPI COMPARISON ===")
        for kpi, data in kpi_comparison.items():
            delta = data["delta"]
            delta_pct = data["delta_pct"]
            sign = "+" if delta > 0 else ""
            lines.append(f"{kpi}: {data['baseline']} → {data['intervention']} ({sign}{delta}, {sign}{delta_pct}%)")
        
        lines.append("")
        
        # Zone pressure summary
        lines.append("=== ZONE PRESSURE COMPARISON ===")
        for zone, data in zone_comparison.items():
            if data["pressure_reduced"]:
                lines.append(f"{zone}: Pressure REDUCED {data['baseline_peak']} → {data['intervention_peak']} ({data['reduction_pct']}%)")
            elif data["baseline_peak"] == data["intervention_peak"]:
                lines.append(f"{zone}: NO CHANGE ({data['baseline_peak']})")
            else:
                lines.append(f"{zone}: Pressure INCREASED {data['baseline_peak']} → {data['intervention_peak']} (+{abs(data['reduction_pct'])}%)")
        
        lines.append("")
        
        # Station changes (new/removed only)
        lines.append("=== STATION CHANGES ===")
        new_stations = [sid for sid, data in station_comparison.items() 
                        if not data["exists_in_baseline"] and data["exists_in_intervention"]]
        removed_stations = [sid for sid, data in station_comparison.items() 
                            if data["exists_in_baseline"] and not data["exists_in_intervention"]]
        
        if new_stations:
            lines.append(f"New stations: {', '.join(new_stations)}")
        if removed_stations:
            lines.append(f"Removed stations: {', '.join(removed_stations)}")
        if not new_stations and not removed_stations:
            lines.append("No stations added or removed")
        
        return "\n".join(lines)
