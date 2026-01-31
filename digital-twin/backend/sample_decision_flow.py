"""
Sample Decision Flow: Complete workflow from interventions to executive recommendation.

Demonstrates:
1. Creating multiple intervention scenarios
2. Scoring each scenario
3. Ranking by score
4. Generating executive recommendation

Run: python sample_decision_flow.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision.decision_scorer import DecisionScorer
from decision.recommendation_generator import RecommendationGenerator
from simulation.scenario_intervention_engine import InterventionType


def main():
    """Run sample decision flow."""
    
    print("=" * 70)
    print("SAMPLE DECISION FLOW: Intervention Scoring & Recommendation")
    print("=" * 70)
    print()
    
    # Initialize decision components
    scorer = DecisionScorer()
    generator = RecommendationGenerator()
    
    # Define intervention scenarios
    scenarios = []
    
    # Scenario 1: Add relief station (high impact)
    print("📊 Scenario 1: Add ST_RELIEF_01 to zone_01")
    intervention1 = {
        "intervention_type": InterventionType.ADD_STATION,
        "station_id": "ST_RELIEF_01",
        "zone_id": "zone_01"
    }
    
    diff1 = {
        "kpi_comparison": {
            "total_swaps": {"baseline": 150, "intervention": 175, "delta": 25, "delta_pct": 16.67},
            "lost_swaps": {"baseline": 12, "intervention": 3, "delta": -9, "delta_pct": -75.0}
        },
        "zone_comparison": {
            "zone_01": {"baseline_peak": 15, "intervention_peak": 7, "pressure_reduced": True, "reduction_pct": -53.33}
        },
        "station_comparison": {
            "ST_RELIEF_01": {"exists_in_baseline": False, "exists_in_intervention": True}
        }
    }
    
    score1 = scorer.score(diff1, intervention_cost=100000)
    print(f"   Score: {score1['total_score']:.2f}/100")
    print(f"   - Operational: {score1['operational_score']:.2f}")
    print(f"   - Capacity: {score1['capacity_score']:.2f}")
    print(f"   - Financial: {score1['financial_score']:.2f}")
    print()
    
    scenarios.append({"intervention": intervention1, "diff": diff1, "score": score1})
    
    # Scenario 2: Modify capacity (medium impact)
    print("📊 Scenario 2: Increase capacity at ST_01_01")
    intervention2 = {
        "intervention_type": InterventionType.MODIFY_CAPACITY,
        "station_id": "ST_01_01"
    }
    
    diff2 = {
        "kpi_comparison": {
            "total_swaps": {"baseline": 150, "intervention": 160, "delta": 10, "delta_pct": 6.67},
            "lost_swaps": {"baseline": 12, "intervention": 7, "delta": -5, "delta_pct": -41.67}
        },
        "zone_comparison": {
            "zone_01": {"baseline_peak": 15, "intervention_peak": 11, "pressure_reduced": True, "reduction_pct": -26.67}
        },
        "station_comparison": {
            "ST_01_01": {"exists_in_baseline": True, "exists_in_intervention": True}
        }
    }
    
    score2 = scorer.score(diff2, intervention_cost=20000)
    print(f"   Score: {score2['total_score']:.2f}/100")
    print(f"   - Operational: {score2['operational_score']:.2f}")
    print(f"   - Capacity: {score2['capacity_score']:.2f}")
    print(f"   - Financial: {score2['financial_score']:.2f}")
    print()
    
    scenarios.append({"intervention": intervention2, "diff": diff2, "score": score2})
    
    # Scenario 3: Optimize swap time (low impact)
    print("📊 Scenario 3: Optimize swap time at ST_01_02")
    intervention3 = {
        "intervention_type": InterventionType.MODIFY_SWAP_TIME,
        "station_id": "ST_01_02"
    }
    
    diff3 = {
        "kpi_comparison": {
            "total_swaps": {"baseline": 150, "intervention": 157, "delta": 7, "delta_pct": 4.67},
            "lost_swaps": {"baseline": 12, "intervention": 10, "delta": -2, "delta_pct": -16.67}
        },
        "zone_comparison": {
            "zone_01": {"baseline_peak": 15, "intervention_peak": 14, "pressure_reduced": True, "reduction_pct": -6.67}
        },
        "station_comparison": {
            "ST_01_02": {"exists_in_baseline": True, "exists_in_intervention": True}
        }
    }
    
    score3 = scorer.score(diff3, intervention_cost=5000)
    print(f"   Score: {score3['total_score']:.2f}/100")
    print(f"   - Operational: {score3['operational_score']:.2f}")
    print(f"   - Capacity: {score3['capacity_score']:.2f}")
    print(f"   - Financial: {score3['financial_score']:.2f}")
    print()
    
    scenarios.append({"intervention": intervention3, "diff": diff3, "score": score3})
    
    # Rank interventions
    print("=" * 70)
    print("RANKING INTERVENTIONS")
    print("=" * 70)
    print()
    
    ranked = generator.rank_interventions(scenarios)
    
    for i, scenario in enumerate(ranked, start=1):
        intervention_name = generator._format_intervention_name(scenario["intervention"])
        score = scenario["score"]["total_score"]
        priority = generator._get_priority_label(score)
        print(f"{i}. {intervention_name}")
        print(f"   Score: {score:.2f}/100 | Priority: {priority}")
        print()
    
    # Generate executive recommendation
    print("=" * 70)
    print("GENERATING EXECUTIVE RECOMMENDATION")
    print("=" * 70)
    print()
    
    recommendation = generator.generate_recommendation(ranked)
    print(recommendation)


if __name__ == "__main__":
    main()
