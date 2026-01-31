"""
Test Decision Layer: Verify scoring and recommendation generation.

Tests:
1. DecisionScorer determinism
2. Scoring component calculations
3. Intervention ranking
4. Recommendation text generation

Run: python test_decision_layer.py
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision.decision_scorer import DecisionScorer
from decision.recommendation_generator import RecommendationGenerator


def create_sample_diff_high_impact():
    """Create sample scenario diff with high impact."""
    return {
        "kpi_comparison": {
            "total_swaps": {
                "baseline": 150,
                "intervention": 175,
                "delta": 25,
                "delta_pct": 16.67
            },
            "lost_swaps": {
                "baseline": 12,
                "intervention": 3,
                "delta": -9,
                "delta_pct": -75.0
            }
        },
        "zone_comparison": {
            "zone_01": {
                "baseline_peak": 15,
                "intervention_peak": 7,
                "pressure_reduced": True,
                "reduction_pct": -53.33
            },
            "zone_02": {
                "baseline_peak": 3,
                "intervention_peak": 3,
                "pressure_reduced": False,
                "reduction_pct": 0.0
            }
        },
        "station_comparison": {
            "ST_RELIEF_01": {
                "exists_in_baseline": False,
                "exists_in_intervention": True
            }
        }
    }


def create_sample_diff_low_impact():
    """Create sample scenario diff with low impact."""
    return {
        "kpi_comparison": {
            "total_swaps": {
                "baseline": 150,
                "intervention": 155,
                "delta": 5,
                "delta_pct": 3.33
            },
            "lost_swaps": {
                "baseline": 12,
                "intervention": 10,
                "delta": -2,
                "delta_pct": -16.67
            }
        },
        "zone_comparison": {
            "zone_01": {
                "baseline_peak": 15,
                "intervention_peak": 13,
                "pressure_reduced": True,
                "reduction_pct": -13.33
            }
        },
        "station_comparison": {
            "ST_01_01": {
                "exists_in_baseline": True,
                "exists_in_intervention": True
            }
        }
    }


def test_scorer_init():
    """Test scorer initializes with default weights."""
    scorer = DecisionScorer()
    assert scorer.weight_operational == 0.4
    assert scorer.weight_capacity == 0.3
    assert scorer.weight_financial == 0.3
    print("✅ test_scorer_init passed")


def test_scorer_weights_validation():
    """Test scorer validates weights sum to 1.0."""
    try:
        scorer = DecisionScorer(weight_operational=0.5, weight_capacity=0.3, weight_financial=0.1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "sum to 1.0" in str(e)
    print("✅ test_scorer_weights_validation passed")


def test_score_high_impact_scenario():
    """Test scoring high-impact scenario."""
    scorer = DecisionScorer()
    diff = create_sample_diff_high_impact()
    
    result = scorer.score(diff, intervention_cost=100000)
    
    # Verify score structure
    assert "total_score" in result
    assert "operational_score" in result
    assert "capacity_score" in result
    assert "financial_score" in result
    assert "breakdown" in result
    
    # High impact should have high scores
    assert result["total_score"] > 50, f"Expected high score, got {result['total_score']}"
    assert result["operational_score"] > 50, "Expected high operational score"
    assert result["capacity_score"] > 50, "Expected high capacity score"
    
    print(f"✅ test_score_high_impact_scenario passed (score: {result['total_score']})")


def test_score_low_impact_scenario():
    """Test scoring low-impact scenario."""
    scorer = DecisionScorer()
    diff = create_sample_diff_low_impact()
    
    result = scorer.score(diff, intervention_cost=10000)
    
    # Low impact should have lower scores
    high_diff = create_sample_diff_high_impact()
    high_result = scorer.score(high_diff, intervention_cost=100000)
    
    assert result["total_score"] < high_result["total_score"], "Low impact should score lower"
    
    print(f"✅ test_score_low_impact_scenario passed (score: {result['total_score']})")


def test_deterministic_scoring():
    """Test same diff produces same score."""
    scorer = DecisionScorer()
    diff = create_sample_diff_high_impact()
    
    result1 = scorer.score(diff, intervention_cost=100000)
    result2 = scorer.score(diff, intervention_cost=100000)
    
    assert result1["total_score"] == result2["total_score"], "Scores should be deterministic"
    assert result1["operational_score"] == result2["operational_score"]
    assert result1["capacity_score"] == result2["capacity_score"]
    assert result1["financial_score"] == result2["financial_score"]
    
    print("✅ test_deterministic_scoring passed")


def test_ranking():
    """Test intervention ranking."""
    generator = RecommendationGenerator()
    
    # Create scenarios with different scores
    scenarios = [
        {"intervention": {"station_id": "ST_A"}, "score": {"total_score": 50.0}},
        {"intervention": {"station_id": "ST_B"}, "score": {"total_score": 75.0}},
        {"intervention": {"station_id": "ST_C"}, "score": {"total_score": 60.0}}
    ]
    
    ranked = generator.rank_interventions(scenarios)
    
    # Verify descending order
    assert ranked[0]["score"]["total_score"] == 75.0, "Top rank should be highest score"
    assert ranked[1]["score"]["total_score"] == 60.0
    assert ranked[2]["score"]["total_score"] == 50.0, "Bottom rank should be lowest score"
    
    print("✅ test_ranking passed")


def test_recommendation_generation():
    """Test recommendation text generation."""
    scorer = DecisionScorer()
    generator = RecommendationGenerator()
    
    # Create sample intervention
    from simulation.scenario_intervention_engine import InterventionType
    
    intervention = {
        "intervention_type": InterventionType.ADD_STATION,
        "station_id": "ST_RELIEF_01",
        "zone_id": "zone_01"
    }
    
    diff = create_sample_diff_high_impact()
    score = scorer.score(diff, intervention_cost=100000)
    
    scenario = {
        "intervention": intervention,
        "diff": diff,
        "score": score
    }
    
    # Generate recommendation
    recommendation = generator.generate_recommendation([scenario])
    
    # Verify key sections present
    assert "EXECUTIVE RECOMMENDATION REPORT" in recommendation
    assert "TOP RECOMMENDATION" in recommendation
    assert "ST_RELIEF_01" in recommendation
    assert "EXPECTED IMPACT" in recommendation
    assert "SCORE BREAKDOWN" in recommendation
    
    print("✅ test_recommendation_generation passed")


def test_multiple_scenarios_ranking():
    """Test ranking multiple scenarios."""
    scorer = DecisionScorer()
    generator = RecommendationGenerator()
    
    # Create multiple scenarios
    from simulation.scenario_intervention_engine import InterventionType
    
    scenarios = []
    
    # Scenario 1: High impact
    intervention1 = {
        "intervention_type": InterventionType.ADD_STATION,
        "station_id": "ST_RELIEF_01"
    }
    diff1 = create_sample_diff_high_impact()
    score1 = scorer.score(diff1, intervention_cost=100000)
    scenarios.append({"intervention": intervention1, "diff": diff1, "score": score1})
    
    # Scenario 2: Low impact
    intervention2 = {
        "intervention_type": InterventionType.MODIFY_CAPACITY,
        "station_id": "ST_01_01"
    }
    diff2 = create_sample_diff_low_impact()
    score2 = scorer.score(diff2, intervention_cost=10000)
    scenarios.append({"intervention": intervention2, "diff": diff2, "score": score2})
    
    # Rank
    ranked = generator.rank_interventions(scenarios)
    
    # Verify high impact is ranked first
    assert ranked[0]["intervention"]["station_id"] == "ST_RELIEF_01", "High impact should rank first"
    
    # Generate recommendation with alternatives
    recommendation = generator.generate_recommendation(ranked)
    
    assert "ALTERNATIVE OPTIONS" in recommendation
    assert "ST_01_01" in recommendation
    
    print("✅ test_multiple_scenarios_ranking passed")


def test_operational_score_calculation():
    """Test operational score calculation logic."""
    scorer = DecisionScorer()
    
    # Perfect scenario: 100% lost swaps reduction
    diff_perfect = {
        "kpi_comparison": {
            "total_swaps": {"baseline": 100, "intervention": 120, "delta": 20},
            "lost_swaps": {"baseline": 10, "intervention": 0, "delta": -10}
        },
        "zone_comparison": {},
        "station_comparison": {}
    }
    
    result = scorer.score(diff_perfect, intervention_cost=50000)
    
    # Should have very high operational score (lost swaps completely eliminated)
    assert result["operational_score"] >= 70, f"Expected high operational score, got {result['operational_score']}"
    
    print(f"✅ test_operational_score_calculation passed (score: {result['operational_score']})")


def test_capacity_score_calculation():
    """Test capacity score calculation logic."""
    scorer = DecisionScorer()
    
    # High pressure reduction scenario
    diff_capacity = {
        "kpi_comparison": {
            "total_swaps": {"baseline": 100, "intervention": 105, "delta": 5},
            "lost_swaps": {"baseline": 5, "intervention": 4, "delta": -1}
        },
        "zone_comparison": {
            "zone_01": {"baseline_peak": 20, "intervention_peak": 8, "reduction_pct": -60.0}
        },
        "station_comparison": {}
    }
    
    result = scorer.score(diff_capacity, intervention_cost=50000)
    
    # Should have high capacity score (60% pressure reduction)
    assert result["capacity_score"] > 0, "Expected positive capacity score"
    
    print(f"✅ test_capacity_score_calculation passed (score: {result['capacity_score']})")


if __name__ == "__main__":
    # Run tests
    test_scorer_init()
    test_scorer_weights_validation()
    test_score_high_impact_scenario()
    test_score_low_impact_scenario()
    test_deterministic_scoring()
    test_ranking()
    test_recommendation_generation()
    test_multiple_scenarios_ranking()
    test_operational_score_calculation()
    test_capacity_score_calculation()
    print("\n🎉 All decision layer tests passed!")
